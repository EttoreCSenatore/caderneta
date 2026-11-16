"""Notificações no app e e-mail com texto mínimo.

Privacidade por padrão (LGPD art. 6º e 14; ECA Digital art. 7º):
- o e-mail nunca leva título, nome de aluno, nota ou qualquer dado do conteúdo, só "você tem novidades" e um link;
- contas de aluno (menores) só recebem notificação dentro do app;
- o horário silencioso (padrão 21h às 7h) adia o e-mail, que sai agrupado em uma mensagem por pessoa;
- notificações antigas são apagadas (ver `limpa_antigas`).
"""

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import mail
from app.config import get_settings
from app.models import (
    STAFF,
    Aluno,
    AnoLetivo,
    Escola,
    Matricula,
    Notificacao,
    Papel,
    Usuario,
    UsuarioPerfil,
    VinculoResponsavel,
)

RETENCAO_LIDAS_DIAS = 90
RETENCAO_MAXIMA_DIAS = 180


def proximo_envio(agora: datetime, fuso: str, inicio: time, fim: time) -> datetime:
    """Se `agora` cai no horário silencioso (no fuso da escola), devolve o fim dele; senão, `agora`."""
    if inicio == fim:
        return agora
    local = agora.astimezone(ZoneInfo(fuso))
    t = local.time()
    silencio = (t >= inicio or t < fim) if inicio > fim else (inicio <= t < fim)
    if not silencio:
        return agora
    alvo = local.replace(hour=fim.hour, minute=fim.minute, second=0, microsecond=0)
    if alvo <= local:
        alvo += timedelta(days=1)
    return alvo.astimezone(UTC)


# --- Quem recebe ----------------------------------------------------------------------------------------


def alunos_do_publico(db: Session, escola_id: uuid.UUID, turma_id: uuid.UUID | None = None) -> list[uuid.UUID]:
    """Alunos matriculados no ano letivo aberto, da turma indicada ou da escola toda."""
    q = (
        select(Matricula.aluno_id)
        .join(AnoLetivo, AnoLetivo.id == Matricula.ano_letivo_id)
        .where(Matricula.escola_id == escola_id, AnoLetivo.aberto.is_(True))
    )
    if turma_id:
        q = q.where(Matricula.turma_id == turma_id)
    return list(db.scalars(q))


def familia_dos_alunos(
    db: Session, escola_id: uuid.UUID, aluno_ids: Iterable[uuid.UUID], *, incluir_alunos: bool = False
) -> dict[uuid.UUID, str]:
    """Responsáveis com conta (vínculo não restrito e que recebem avisos) e, se pedido, as contas dos alunos."""
    ids = list(aluno_ids)
    res: dict[uuid.UUID, str] = {}
    q1 = (
        select(Usuario.id, Usuario.nome)
        .join(VinculoResponsavel, VinculoResponsavel.usuario_id == Usuario.id)
        .where(
            VinculoResponsavel.escola_id == escola_id,
            VinculoResponsavel.aluno_id.in_(ids),
            VinculoResponsavel.restrito.is_(False),
            VinculoResponsavel.recebe_avisos.is_(True),
        )
    )
    for uid, nome in db.execute(q1):
        res[uid] = nome
    if incluir_alunos:
        q2 = select(Usuario.id, Usuario.nome).join(Aluno, Aluno.usuario_id == Usuario.id).where(Aluno.id.in_(ids))
        for uid, nome in db.execute(q2):
            res[uid] = nome
    return res


def equipe_da_escola(db: Session, escola_id: uuid.UUID) -> set[uuid.UUID]:
    return set(
        db.scalars(
            select(UsuarioPerfil.usuario_id).where(
                UsuarioPerfil.escola_id == escola_id,
                UsuarioPerfil.ativo.is_(True),
                UsuarioPerfil.papel.in_(list(STAFF)),
            )
        )
    )


# --- Criar notificações ---------------------------------------------------------------------------------


def notificar(
    db: Session,
    *,
    escola_id: uuid.UUID,
    usuarios: Iterable[uuid.UUID],
    tipo: str,
    titulo: str,
    corpo: str = "",
    url: str = "/notificacoes",
    excluir: uuid.UUID | None = None,
    agora: datetime | None = None,
) -> int:
    """Cria uma notificação por usuário (e marca o e-mail como pendente quando permitido)."""
    agora = agora or datetime.now(UTC)
    alvo = {u for u in usuarios if u != excluir}
    if not alvo:
        return 0
    escola = db.get(Escola, escola_id)
    fuso = escola.fuso if escola else "America/Sao_Paulo"
    papeis: dict[uuid.UUID, set[Papel]] = {}
    for uid, papel in db.execute(
        select(UsuarioPerfil.usuario_id, UsuarioPerfil.papel).where(
            UsuarioPerfil.usuario_id.in_(alvo), UsuarioPerfil.escola_id == escola_id
        )
    ):
        papeis.setdefault(uid, set()).add(papel)
    so_aluno = {uid for uid, ps in papeis.items() if ps == {Papel.aluno}}
    n = 0
    for u in db.scalars(select(Usuario).where(Usuario.id.in_(alvo), Usuario.ativo.is_(True))):
        quer_email = u.notif_email and u.id not in so_aluno
        quer_push = u.id not in so_aluno  # contas de aluno (menores) não recebem push; o worker confere se há aparelho
        db.add(
            Notificacao(
                escola_id=escola_id,
                usuario_id=u.id,
                tipo=tipo,
                titulo=titulo[:200],
                corpo=corpo[:300],
                url=url,
                criado_em=agora,
                email_pendente=quer_email,
                push_pendente=quer_push,
                enviar_apos=(
                    proximo_envio(agora, fuso, u.silencio_inicio, u.silencio_fim) if quer_email or quer_push else None
                ),
            )
        )
        n += 1
    return n


# --- Worker (roda com o papel dono do banco, sem RLS) -----------------------------------------------------


def envia_emails(db: Session, agora: datetime | None = None) -> int:
    """Um e-mail genérico por pessoa, agrupando tudo o que já passou do horário silencioso."""
    agora = agora or datetime.now(UTC)
    pendentes = list(
        db.scalars(
            select(Notificacao).where(
                Notificacao.email_pendente.is_(True),
                Notificacao.email_enviado_em.is_(None),
                Notificacao.enviar_apos <= agora,
            )
        )
    )
    por_usuario: dict[uuid.UUID, list[Notificacao]] = {}
    for n in pendentes:
        por_usuario.setdefault(n.usuario_id, []).append(n)
    base = get_settings().public_url.rstrip("/")
    enviados = 0
    for uid, itens in por_usuario.items():
        u = db.get(Usuario, uid)
        if u and u.ativo and u.notif_email:
            qtd = len([i for i in itens if i.lida_em is None])
            if qtd:
                assunto = "Caderneta: você tem novidades" if qtd > 1 else "Caderneta: você tem uma novidade"
                mail.enviar(
                    u.email,
                    assunto,
                    f"Olá! Há {qtd} {'novidades' if qtd > 1 else 'novidade'} para você na Caderneta.\n"
                    f"Entre para ver: {base}/notificacoes\n\n"
                    "Por segurança, este e-mail não traz o conteúdo. "
                    "Para parar de receber e-mails, desligue-os em Notificações > Preferências.",
                )
                enviados += 1
        for i in itens:
            i.email_enviado_em = agora
            i.email_pendente = False
    return enviados


def envia_pushes(db: Session, agora: datetime | None = None) -> dict[str, int]:
    """Um push vazio por aparelho de quem tem novidade não lida e já passou do horário silencioso.

    Aparelho que responde 404/410 não existe mais e a inscrição é apagada. Falha temporária mantém a pendência para a
    próxima rodada. Quem não tem aparelho cadastrado simplesmente encerra a pendência.
    """
    from app import push
    from app.models import PushInscricao

    agora = agora or datetime.now(UTC)
    if not push.ativo():
        return {"pushes": 0, "inscricoes_removidas": 0}
    pendentes = list(
        db.scalars(
            select(Notificacao).where(
                Notificacao.push_pendente.is_(True),
                Notificacao.push_enviado_em.is_(None),
                Notificacao.enviar_apos <= agora,
            )
        )
    )
    por_usuario: dict[uuid.UUID, list[Notificacao]] = {}
    for n in pendentes:
        por_usuario.setdefault(n.usuario_id, []).append(n)
    enviados = removidas = 0
    for uid, itens in por_usuario.items():
        falhou = False
        nao_lidas = any(i.lida_em is None for i in itens)
        u = db.get(Usuario, uid)
        if nao_lidas and u and u.ativo:
            for ins in list(db.scalars(select(PushInscricao).where(PushInscricao.usuario_id == uid))):
                status = push.envia(ins.endpoint)
                if status in (404, 410):
                    db.delete(ins)
                    removidas += 1
                elif 200 <= status < 300:
                    ins.ultimo_uso_em = agora
                    enviados += 1
                else:
                    falhou = True
        if not falhou:
            for i in itens:
                i.push_pendente, i.push_enviado_em = False, agora
    return {"pushes": enviados, "inscricoes_removidas": removidas}


def limpa_inscricoes(db: Session, agora: datetime | None = None) -> int:
    """Retenção: inscrição sem uso há `retencao_push_dias` ou de conta desativada é apagada."""
    from app.models import PushInscricao

    agora = agora or datetime.now(UTC)
    corte = agora - timedelta(days=get_settings().retencao_push_dias)
    r = db.execute(
        delete(PushInscricao).where(
            (PushInscricao.ultimo_uso_em < corte)
            | PushInscricao.usuario_id.in_(select(Usuario.id).where(Usuario.ativo.is_(False)))
        )
    )
    return r.rowcount or 0


def limpa_antigas(db: Session, agora: datetime | None = None) -> int:
    """Retenção: lidas somem após 90 dias; qualquer notificação após 180."""
    agora = agora or datetime.now(UTC)
    r = db.execute(
        delete(Notificacao).where(
            (Notificacao.lida_em.is_not(None) & (Notificacao.criado_em < agora - timedelta(days=RETENCAO_LIDAS_DIAS)))
            | (Notificacao.criado_em < agora - timedelta(days=RETENCAO_MAXIMA_DIAS))
        )
    )
    return r.rowcount or 0


def publica_agendados(db: Session, agora: datetime | None = None) -> int:
    """Avisos agendados que chegaram na hora de sair: notifica o público e marca como notificado."""
    from app.models import Aviso

    agora = agora or datetime.now(UTC)
    total = 0
    for a in db.scalars(
        select(Aviso).where(Aviso.publicar_em <= agora, Aviso.notificado_em.is_(None), Aviso.arquivado.is_(False))
    ):
        total += notifica_aviso(db, a, agora)
    return total


def notifica_aviso(db: Session, aviso, agora: datetime | None = None) -> int:
    agora = agora or datetime.now(UTC)
    familia = familia_dos_alunos(
        db, aviso.escola_id, alunos_do_publico(db, aviso.escola_id, aviso.turma_id), incluir_alunos=True
    )
    aviso.notificado_em = agora
    return notificar(
        db,
        escola_id=aviso.escola_id,
        usuarios=familia,
        tipo="aviso",
        titulo="Novo aviso da escola",
        corpo=aviso.titulo,
        url="/avisos",
        excluir=aviso.autor_id,
        agora=agora,
    )


def processar(db: Session, agora: datetime | None = None) -> dict[str, int]:
    """Uma rodada do worker: libera avisos agendados, envia e-mails devidos e aplica a retenção."""
    from app.retencao import elimina_vencidos

    r = {
        "avisos": publica_agendados(db, agora),
        "emails": envia_emails(db, agora),
        "apagadas": limpa_antigas(db, agora),
        "inscricoes_apagadas": limpa_inscricoes(db, agora),
    } | envia_pushes(db, agora)
    return r | {f"eliminados_{k}": v for k, v in elimina_vencidos(db, agora).items()}
