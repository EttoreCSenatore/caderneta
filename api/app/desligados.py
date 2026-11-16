"""Alunos e usuários desligados: apagar o que é complementar e anonimizar contas, com aviso antes.

Aluno desligado (transferido, concluiu, arquivado):
- **fica** o núcleo histórico: nome, nascimento, RA, matrículas, notas, frequência (só o status) e os históricos
  emitidos;
- **sai** depois do prazo: ficha de saúde, anotações e versões, conversas, mensagens e anexos, contatos dos
  responsáveis, respostas de autorização, CPF e as justificativas de falta (texto livre, que pode revelar saúde).
Usuário desligado (funcionário, responsável ou conta de aluno): a conta é **anonimizada** quando não tem mais nenhum
perfil ativo, e o que ele escreveu continua, atribuído a "Ex-usuário".

Antes de qualquer apagamento a direção é avisada (e as pessoas atingidas recebem um e-mail sem conteúdo), com opção
de adiar. Tudo fica na auditoria, sem dados pessoais nos detalhes.
"""

import uuid
from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app import mail
from app.audit import registrar
from app.models import (
    Aluno,
    Anotacao,
    AutorizacaoResposta,
    CalendarioToken,
    Conversa,
    Convite,
    Escola,
    FichaSaude,
    Frequencia,
    Matricula,
    Mensagem,
    MensagemAnexo,
    Notificacao,
    Papel,
    PushInscricao,
    SituacaoAluno,
    TokenSenha,
    Usuario,
    UsuarioPerfil,
    VinculoResponsavel,
)
from app.notificacoes import notificar
from app.retencao import _apaga_arquivos

NOME_ANONIMO = "Ex-usuário"


def data_prevista(desligado_em: datetime, dias: int, adiada: date | None) -> date:
    """Dia em que o apagamento acontece: o prazo da escola ou o adiamento, o que for mais tarde."""
    natural = (desligado_em + timedelta(days=dias)).date()
    return max(natural, adiada) if adiada else natural


def avisado_a_tempo(avisada_em: datetime | None, aviso_dias: int, agora: datetime) -> bool:
    """O apagamento só ocorre depois de a direção ter sido avisada com pelo menos `aviso_dias` de antecedência."""
    return avisada_em is not None and avisada_em <= agora - timedelta(days=aviso_dias)


# --- Aluno ----------------------------------------------------------------------------------------------------


def purga_aluno(db: Session, aluno: Aluno, usuario_id: uuid.UUID | None = None, agora: datetime | None = None) -> dict:
    """Apaga os dados complementares do aluno. Mantém o núcleo histórico. Idempotente."""
    agora = agora or datetime.now(UTC)
    eid, aid = aluno.escola_id, aluno.id
    n: Counter[str] = Counter()

    n["ficha_saude"] = db.execute(delete(FichaSaude).where(FichaSaude.aluno_id == aid)).rowcount or 0
    n["anotacoes"] = db.execute(delete(Anotacao).where(Anotacao.aluno_id == aid)).rowcount or 0  # versões em cascata
    conversas = list(db.scalars(select(Conversa.id).where(Conversa.aluno_id == aid)))
    mensagens = select(Mensagem.id).where(Mensagem.conversa_id.in_(conversas))
    arquivos_a_apagar = set(
        db.scalars(select(MensagemAnexo.arquivo_id).where(MensagemAnexo.mensagem_id.in_(mensagens)))
    )
    n["conversas"] = len(conversas)
    if conversas:
        db.execute(delete(Conversa).where(Conversa.id.in_(conversas)))  # mensagens, anexos e leituras em cascata
        db.flush()
        _apaga_arquivos(db, arquivos_a_apagar)
    n["autorizacoes"] = db.execute(delete(AutorizacaoResposta).where(AutorizacaoResposta.aluno_id == aid)).rowcount or 0
    db.execute(delete(Convite).where(Convite.aluno_id == aid))

    responsaveis = set(
        db.scalars(
            select(VinculoResponsavel.usuario_id).where(
                VinculoResponsavel.aluno_id == aid, VinculoResponsavel.usuario_id.is_not(None)
            )
        )
    )
    n["contatos"] = db.execute(delete(VinculoResponsavel).where(VinculoResponsavel.aluno_id == aid)).rowcount or 0
    db.flush()

    matriculas = select(Matricula.id).where(Matricula.aluno_id == aid)
    n["justificativas"] = (
        db.execute(
            update(Frequencia)
            .where(Frequencia.matricula_id.in_(matriculas), Frequencia.justificativa.is_not(None))
            .values(justificativa=None)
        ).rowcount
        or 0
    )
    aluno.cpf = None
    aluno.purgado_em = agora

    # as contas ligadas a este aluno perdem o acesso: a do próprio aluno e as de responsáveis sem outro aluno na escola
    contas = {aluno.usuario_id} if aluno.usuario_id else set()
    for uid in responsaveis:
        restante = db.scalar(
            select(func.count())
            .select_from(VinculoResponsavel)
            .where(VinculoResponsavel.usuario_id == uid, VinculoResponsavel.escola_id == eid)
        )
        if not restante:
            contas.add(uid)
    for p in db.scalars(
        select(UsuarioPerfil).where(
            UsuarioPerfil.escola_id == eid,
            UsuarioPerfil.usuario_id.in_(contas),
            UsuarioPerfil.papel.in_([Papel.aluno, Papel.responsavel]),
            UsuarioPerfil.ativo.is_(True),
        )
    ):
        p.ativo = False  # o evento do modelo registra o desligamento e inicia a contagem da conta
    n["perfis_desligados"] = len(contas)

    registrar(
        db,
        "desligados.purgar_aluno",
        escola_id=eid,
        usuario_id=usuario_id,
        entidade="aluno",
        entidade_id=aid,
        detalhes=dict(n),
    )
    return dict(n)


# --- Usuário --------------------------------------------------------------------------------------------------


def anonimiza_usuario(db: Session, u: Usuario, agora: datetime | None = None) -> None:
    """Remove a identidade da conta e tudo que é só dela. O que a pessoa escreveu fica, atribuído a 'Ex-usuário'."""
    agora = agora or datetime.now(UTC)
    antigo_email = str(u.email)
    perfis = list(db.scalars(select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == u.id)))
    escolas = {p.escola_id for p in perfis}
    for p in perfis:
        db.execute(delete(CalendarioToken).where(CalendarioToken.perfil_id == p.id))
    from app.models import Sessao

    db.execute(delete(Sessao).where(Sessao.usuario_id == u.id))
    db.execute(delete(TokenSenha).where(TokenSenha.usuario_id == u.id))
    db.execute(delete(PushInscricao).where(PushInscricao.usuario_id == u.id))
    db.execute(delete(Notificacao).where(Notificacao.usuario_id == u.id))
    db.execute(delete(Convite).where(Convite.email == antigo_email))
    db.execute(update(VinculoResponsavel).where(VinculoResponsavel.usuario_id == u.id).values(usuario_id=None))
    db.execute(update(Aluno).where(Aluno.usuario_id == u.id).values(usuario_id=None))
    u.nome, u.email, u.telefone = NOME_ANONIMO, f"removido-{u.id}@anonimo.invalid", None
    u.senha_hash, u.totp_secret_enc, u.totp_ativo = None, None, False
    u.ativo, u.anonimizado_em = False, agora
    for eid in escolas:
        registrar(
            db, "desligados.anonimizar_usuario", escola_id=eid, usuario_id=None, entidade="usuario", entidade_id=u.id
        )


# --- Worker ---------------------------------------------------------------------------------------------------


def _aviso_por_email(para: str | None, escola: str, tipo: str, dias: int) -> None:
    if not para:
        return
    if tipo == "usuario":
        texto = (
            f"Olá! O seu acesso à Caderneta da escola {escola} foi encerrado. Os dados da sua conta serão anonimizados "
            f"em cerca de {dias} dias. Se tiver dúvidas ou precisar de uma cópia dos seus dados, fale com a escola."
        )
    else:
        texto = (
            f"Olá! O aluno vinculado a este e-mail na escola {escola} foi desligado. Os dados complementares dele "
            f"(saúde, anotações, mensagens e contatos) serão apagados em cerca de {dias} dias. Se quiser uma cópia, "
            "peça à escola antes dessa data."
        )
    mail.enviar(para, "Caderneta: aviso sobre seus dados", texto)


def processa_desligados(db: Session, agora: datetime | None = None) -> dict[str, int]:
    """Uma rodada: avisa quem está perto do prazo e apaga ou anonimiza o que venceu e foi avisado (papel dono)."""
    agora = agora or datetime.now(UTC)
    hoje = agora.date()
    r = Counter()
    avisos: dict[uuid.UUID, Counter[str]] = {}

    for escola in db.scalars(select(Escola)):
        aviso = escola.aviso_desligados_dias
        # alunos
        alunos = db.scalars(
            select(Aluno).where(
                Aluno.escola_id == escola.id,
                Aluno.situacao != SituacaoAluno.ativo,
                Aluno.purgado_em.is_(None),
                Aluno.desligado_em.is_not(None),
            )
        )
        for a in list(alunos):
            prevista = data_prevista(a.desligado_em, escola.retencao_aluno_desligado_dias, a.purga_adiada_ate)
            if a.purga_avisada_em is None and hoje >= prevista - timedelta(days=aviso):
                a.purga_avisada_em = agora
                avisos.setdefault(escola.id, Counter())["alunos"] += 1
                for v in db.scalars(
                    select(VinculoResponsavel).where(
                        VinculoResponsavel.aluno_id == a.id, VinculoResponsavel.restrito.is_(False)
                    )
                ):
                    _aviso_por_email(v.email, escola.nome, "aluno", aviso)
                r["avisos_alunos"] += 1
            elif hoje >= prevista and avisado_a_tempo(a.purga_avisada_em, aviso, agora):
                purga_aluno(db, a, None, agora)
                r["alunos_purgados"] += 1
        # perfis de usuários desligados
        perfis = db.scalars(
            select(UsuarioPerfil).where(
                UsuarioPerfil.escola_id == escola.id,
                UsuarioPerfil.ativo.is_(False),
                UsuarioPerfil.desligado_em.is_not(None),
            )
        )
        for p in list(perfis):
            prevista = data_prevista(p.desligado_em, escola.retencao_usuario_desligado_dias, p.anonimizacao_adiada_ate)
            if p.anonimizacao_avisada_em is None and hoje >= prevista - timedelta(days=aviso):
                p.anonimizacao_avisada_em = agora
                avisos.setdefault(escola.id, Counter())["usuarios"] += 1
                if p.usuario.anonimizado_em is None:
                    _aviso_por_email(str(p.usuario.email), escola.nome, "usuario", aviso)
                r["avisos_usuarios"] += 1
    db.flush()

    # anonimização é por conta: só quando TODOS os perfis estão desligados, vencidos e avisados
    for u in db.scalars(select(Usuario).where(Usuario.anonimizado_em.is_(None))):
        perfis = list(db.scalars(select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == u.id)))
        if not perfis or any(p.ativo for p in perfis):
            continue
        ok = True
        for p in perfis:
            esc = db.get(Escola, p.escola_id)
            if p.desligado_em is None or esc is None:
                ok = False
                break
            prevista = data_prevista(p.desligado_em, esc.retencao_usuario_desligado_dias, p.anonimizacao_adiada_ate)
            if hoje < prevista or not avisado_a_tempo(p.anonimizacao_avisada_em, esc.aviso_desligados_dias, agora):
                ok = False
                break
        if ok:
            anonimiza_usuario(db, u, agora)
            r["usuarios_anonimizados"] += 1

    for escola_id, c in avisos.items():  # um aviso por escola, para a direção
        admins = set(
            db.scalars(
                select(UsuarioPerfil.usuario_id).where(
                    UsuarioPerfil.escola_id == escola_id,
                    UsuarioPerfil.ativo.is_(True),
                    UsuarioPerfil.papel == Papel.admin,
                )
            )
        )
        partes = []
        if c["alunos"]:
            partes.append(f"{c['alunos']} aluno(s)")
        if c["usuarios"]:
            partes.append(f"{c['usuarios']} usuário(s)")
        escola = db.get(Escola, escola_id)
        notificar(
            db,
            escola_id=escola_id,
            usuarios=admins,
            tipo="desligados",
            titulo="Dados de desligados serão apagados em breve",
            corpo=f"{' e '.join(partes)} em cerca de {escola.aviso_desligados_dias} dias. Revise em Desligados.",
            url="/desligados",
            agora=agora,
        )
    return dict(r)
