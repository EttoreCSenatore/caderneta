"""Exportação dos dados de um titular (LGPD art. 18, II e V): conteúdo, origem, finalidade e destinatários.

Regras de minimização na exportação:
- só o que o próprio titular já pode ver no app (notas só as publicadas; anotações só as visíveis às famílias);
- dados de **outras pessoas** ficam de fora ou só com o nome e o papel (contatos de outros responsáveis, nome de
  professores, mensagens de outros);
- ficha de saúde só para o responsável do aluno (a conta do próprio aluno não a vê no app);
- o CPF e as mensagens aparecem apenas para quem é titular deles.
Anotações pedagógicas e reservadas **não** entram: se o titular tem direito a elas é decisão jurídica (gap T19).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Aluno,
    AnoLetivo,
    Anotacao,
    Atribuicao,
    Aula,
    Autorizacao,
    AutorizacaoResposta,
    Avaliacao,
    Aviso,
    AvisoLeitura,
    Conversa,
    Disciplina,
    FichaSaude,
    Frequencia,
    HistoricoEmitido,
    Matricula,
    Mensagem,
    Nota,
    Notificacao,
    Papel,
    PushInscricao,
    Sessao,
    TipoAnotacao,
    Turma,
    Usuario,
    UsuarioPerfil,
    VinculoResponsavel,
)
from app.security import decifra, decifra_json

TRATAMENTO = {
    "controlador": "A escola. A Caderneta é a operadora, que trata os dados em nome da escola.",
    "origem": "Os dados vêm da escola (cadastro e secretaria), dos responsáveis, dos professores e do uso do app.",
    "finalidades": [
        "Execução do serviço educacional: notas, frequência, avisos, calendário, provas e histórico escolar",
        "Comunicação entre a escola e as famílias, incluindo notificações",
        "Segurança da conta (login, verificação em duas etapas, limite de tentativas)",
        "Cumprimento de obrigação legal e escolar (guarda do histórico escolar)",
    ],
    "destinatarios": "Equipe da escola e professores do aluno, conforme o papel de cada um; responsáveis do aluno. "
    "Os dados não são vendidos nem compartilhados com anunciantes. "
    "Provedores de hospedagem e e-mail atuam como suboperadores.",
    "retencao": "Os dados são guardados enquanto o aluno ou o usuário está ativo. Depois do desligamento, o histórico "
    "(notas, frequência, documentos emitidos) é mantido e o restante é apagado após o prazo definido pela escola, "
    "com aviso antes.",
}


def _iso(v: datetime | None) -> str | None:
    return v.isoformat() if v else None


def exporta_usuario(db: Session, u: Usuario) -> dict:
    """Dados da conta e da atividade do usuário na escola do perfil ativo (o RLS limita à escola)."""
    perfis = db.scalars(select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == u.id))
    vinculos = db.execute(
        select(VinculoResponsavel, Aluno)
        .join(Aluno, Aluno.id == VinculoResponsavel.aluno_id)
        .where(VinculoResponsavel.usuario_id == u.id)
    ).all()
    leituras = db.execute(
        select(AvisoLeitura, Aviso.titulo)
        .join(Aviso, Aviso.id == AvisoLeitura.aviso_id)
        .where(AvisoLeitura.usuario_id == u.id)
    ).all()
    respostas = db.execute(
        select(AutorizacaoResposta, Autorizacao.titulo, Aluno)
        .join(Autorizacao, Autorizacao.id == AutorizacaoResposta.autorizacao_id)
        .join(Aluno, Aluno.id == AutorizacaoResposta.aluno_id)
        .where(AutorizacaoResposta.usuario_id == u.id)
    ).all()
    minhas_msgs = db.execute(
        select(Mensagem, Conversa.assunto)
        .join(Conversa, Conversa.id == Mensagem.conversa_id)
        .where(Mensagem.autor_id == u.id)
    ).all()
    return {
        "conta": {
            "nome": u.nome,
            "email": u.email,
            "telefone": u.telefone,
            "criada_em": _iso(u.criado_em),
            "verificacao_em_duas_etapas": u.totp_ativo,
            "preferencias": {
                "email_de_avisos": u.notif_email,
                "silencio_das": str(u.silencio_inicio),
                "silencio_ate": str(u.silencio_fim),
            },
        },
        "perfis": [{"papel": p.papel, "ativo": p.ativo, "desligado_em": _iso(p.desligado_em)} for p in perfis],
        "aparelhos_e_sessoes": {
            "sessoes_abertas": len(list(db.scalars(select(Sessao.id).where(Sessao.usuario_id == u.id)))),
            "aparelhos_com_push": len(
                list(db.scalars(select(PushInscricao.id).where(PushInscricao.usuario_id == u.id)))
            ),
        },
        "vinculos_como_responsavel": [
            {
                "aluno": f"{a.nome} {a.sobrenome}",
                "tipo": v.tipo,
                "telefone": v.telefone,
                "email": v.email,
                "recebe_avisos": v.recebe_avisos,
                "emergencia": v.emergencia,
                "pode_buscar": v.pode_buscar,
            }
            for v, a in vinculos
        ],
        "avisos_lidos": [
            {"aviso": titulo, "lido_em": _iso(lei.lido_em), "ciente_em": _iso(lei.ciente_em)}
            for lei, titulo in leituras
        ],
        "autorizacoes_respondidas": [
            {
                "autorizacao": titulo,
                "aluno": f"{a.nome} {a.sobrenome}",
                "autoriza": r.autoriza,
                "observacao": r.observacao,
                "respondido_em": _iso(r.respondido_em),
            }
            for r, titulo, a in respostas
        ],
        "mensagens_que_voce_escreveu": [
            {"conversa": assunto, "texto": m.corpo, "enviada_em": _iso(m.criado_em)} for m, assunto in minhas_msgs
        ],
        "notificacoes": [
            {"titulo": n.titulo, "texto": n.corpo, "criada_em": _iso(n.criado_em), "lida_em": _iso(n.lida_em)}
            for n in db.scalars(
                select(Notificacao).where(Notificacao.usuario_id == u.id).order_by(Notificacao.criado_em)
            )
        ],
    }


def exporta_aluno(db: Session, a: Aluno, papel_solicitante: Papel, solicitante_id: uuid.UUID | None) -> dict:
    """Dados do aluno para o próprio aluno, seus responsáveis ou a direção atendendo um pedido."""
    matriculas = db.execute(
        select(Matricula, Turma.nome, AnoLetivo.ano)
        .join(Turma, Turma.id == Matricula.turma_id)
        .join(AnoLetivo, AnoLetivo.id == Matricula.ano_letivo_id)
        .where(Matricula.aluno_id == a.id)
        .order_by(AnoLetivo.ano)
    ).all()
    mids = {m.id: (ano, turma) for m, turma, ano in matriculas}
    notas = db.execute(
        select(Nota, Avaliacao, Disciplina.nome)
        .join(Avaliacao, Avaliacao.id == Nota.avaliacao_id)
        .join(Atribuicao, Atribuicao.id == Avaliacao.atribuicao_id)
        .join(Disciplina, Disciplina.id == Atribuicao.disciplina_id)
        .where(Nota.matricula_id.in_(mids), Avaliacao.publicada.is_(True))
    ).all()
    freq = db.execute(
        select(Frequencia, Aula.data, Aula.quantidade, Disciplina.nome)
        .join(Aula, Aula.id == Frequencia.aula_id)
        .join(Atribuicao, Atribuicao.id == Aula.atribuicao_id)
        .join(Disciplina, Disciplina.id == Atribuicao.disciplina_id)
        .where(Frequencia.matricula_id.in_(mids))
        .order_by(Aula.data)
    ).all()
    anotacoes = [
        x
        for x in db.scalars(select(Anotacao).where(Anotacao.aluno_id == a.id, Anotacao.removida_em.is_(None)))
        if x.tipo == TipoAnotacao.elogio or (x.tipo == TipoAnotacao.ocorrencia and x.visivel_responsaveis)
    ]
    autoriz = db.execute(
        select(AutorizacaoResposta, Autorizacao.titulo)
        .join(Autorizacao, Autorizacao.id == AutorizacaoResposta.autorizacao_id)
        .where(AutorizacaoResposta.aluno_id == a.id)
    ).all()
    vinculos = list(db.scalars(select(VinculoResponsavel).where(VinculoResponsavel.aluno_id == a.id)))
    saida: dict = {
        "aluno": {
            "nome": a.nome,
            "sobrenome": a.sobrenome,
            "nome_social": a.nome_social,
            "data_nascimento": a.data_nascimento.isoformat(),
            "ra": a.ra,
            "cpf": a.cpf,
            "situacao": a.situacao,
        },
        "matriculas": [{"ano": ano, "turma": turma, "situacao": m.situacao} for m, turma, ano in matriculas],
        "notas_publicadas": [
            {
                "ano": mids[n.matricula_id][0],
                "disciplina": d,
                "avaliacao": av.nome,
                "tipo": av.tipo,
                "data": av.data.isoformat() if av.data else None,
                "valor": float(n.valor) if n.valor is not None else None,
                "situacao": n.status,
                "nota_maxima": float(av.nota_maxima),
            }
            for n, av, d in notas
        ],
        "frequencia": [
            {
                "ano": mids[f.matricula_id][0],
                "data": data.isoformat(),
                "disciplina": d,
                "aulas": q,
                "situacao": f.status,
                "justificativa": f.justificativa,
            }
            for f, data, q, d in freq
        ],
        "anotacoes_visiveis_as_familias": [
            {"tipo": x.tipo, "texto": x.corpo, "data": _iso(x.criado_em), "autoria": "Professor(a) ou equipe da escola"}
            for x in anotacoes
        ],
        "autorizacoes": [
            {
                "autorizacao": titulo,
                "autoriza": r.autoriza,
                "observacao": r.observacao,
                "respondido_em": _iso(r.respondido_em),
            }
            for r, titulo in autoriz
        ],
        "responsaveis": [
            # contato de outros responsáveis é dado de terceiros: só tipo e nome (o próprio vínculo vem completo)
            {"tipo": v.tipo, "nome": v.nome}
            | ({"telefone": v.telefone, "email": v.email} if solicitante_id and v.usuario_id == solicitante_id else {})
            for v in vinculos
        ],
        "historicos_escolares_emitidos": [
            {"emitido_em": _iso(h.emitido_em), "codigo": h.codigo}
            for h in db.scalars(select(HistoricoEmitido).where(HistoricoEmitido.aluno_id == a.id))
        ],
    }
    if papel_solicitante != Papel.aluno:  # a conta do aluno não vê a ficha de saúde no app; pede à escola
        ficha = db.get(FichaSaude, a.id)
        saida["saude"] = (
            decifra_json(ficha.dados_enc, str(a.id))
            | {"alerta": decifra(ficha.alerta_enc, f"alerta:{a.id}") if ficha.alerta_enc else ""}
            if ficha
            else None
        )
    return saida


def pacote(titulo: str, conteudo: dict) -> dict:
    return {
        "gerado_em": datetime.now(UTC).isoformat(),
        "titulo": titulo,
        "aviso": "Estes são os seus dados tratados pela Caderneta, em formato estruturado (JSON). "
        "Dados de outras pessoas "
        "(contatos de outros responsáveis, nomes de professores) foram omitidos para protegê-las.",
        "como_os_dados_sao_tratados": TRATAMENTO,
        **conteudo,
    }
