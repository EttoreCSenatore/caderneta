"""Consultas compartilhadas do M2: regra de média do ano, acesso ao diário e cálculo de médias da turma."""

import uuid
from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from app.deps import Contexto
from app.medias import NotaLancada, Regra, media_periodo
from app.models import (
    STAFF,
    Aluno,
    Atribuicao,
    Avaliacao,
    Matricula,
    Nota,
    Papel,
    Periodo,
    RegraMedia,
    Turma,
)


def regra_do_ano(ctx: Contexto, ano_letivo_id: uuid.UUID) -> Regra:
    r = ctx.db.get(RegraMedia, ano_letivo_id)
    if not r:
        return Regra()
    return Regra(
        tipo_media=r.tipo_media,
        pesos_periodos=tuple(Decimal(str(p)) for p in r.pesos_periodos) if r.pesos_periodos else None,
        recuperacao=r.recuperacao,
        arredondamento=r.arredondamento,
        nota_maxima=r.nota_maxima,
        media_aprovacao=r.media_aprovacao,
        frequencia_minima=r.frequencia_minima,
    )


def atribuicao_do_diario(ctx: Contexto, atribuicao_id: uuid.UUID) -> tuple[Atribuicao, Turma]:
    """Leitura: equipe vê qualquer diário; professor só os seus. 404 para o resto."""
    a = ctx.db.get(Atribuicao, atribuicao_id)
    if not a or not (ctx.papel in STAFF or (ctx.papel == Papel.professor and a.professor_id == ctx.usuario.id)):
        raise HTTPException(404, "Diário não encontrado.")
    turma = ctx.db.get(Turma, a.turma_id)
    assert turma is not None
    return a, turma


def pode_escrever(ctx: Contexto, a: Atribuicao, periodo: Periodo, justificativa: str | None) -> bool:
    """Professor escreve no próprio diário com o período aberto. A direção corrige qualquer diário, sempre
    com justificativa (auditada). Coordenação só lê. Retorna True se for uma correção a ser auditada."""
    if ctx.papel == Papel.professor and a.professor_id == ctx.usuario.id and not periodo.fechado:
        return False
    if ctx.papel == Papel.admin:
        if not (justificativa and justificativa.strip()):
            raise HTTPException(422, "Informe a justificativa da correção.")
        return True
    if periodo.fechado:
        raise HTTPException(409, f"O {periodo.nome} está fechado. Peça à direção para corrigir.")
    raise HTTPException(403, "Sem permissão para esta ação.")


def periodo_do_ano(ctx: Contexto, periodo_id: uuid.UUID, turma: Turma) -> Periodo:
    p = ctx.db.get(Periodo, periodo_id)
    if not p or p.ano_letivo_id != turma.ano_letivo_id:
        raise HTTPException(404, "Período não encontrado.")
    return p


def matriculas_da_turma(ctx: Contexto, turma: Turma) -> list[tuple[Matricula, Aluno]]:
    rows = ctx.db.execute(
        select(Matricula, Aluno)
        .join(Aluno, Aluno.id == Matricula.aluno_id)
        .where(Matricula.turma_id == turma.id, Aluno.situacao == "ativo")
        .order_by(Aluno.nome, Aluno.sobrenome)
    ).all()
    return [(m, a) for m, a in rows]


def nota_lancada(av: Avaliacao, n: Nota | None) -> NotaLancada:
    if n is None:
        return NotaLancada(None, av.peso, av.nota_maxima, recuperacao=av.recuperacao)
    return NotaLancada(n.valor, av.peso, av.nota_maxima, n.status, av.recuperacao)


def medias_do_periodo(
    ctx: Contexto, avaliacoes: list[Avaliacao], matricula_ids: list[uuid.UUID], regra: Regra
) -> dict[uuid.UUID, dict]:
    notas = ctx.db.scalars(select(Nota).where(Nota.avaliacao_id.in_([a.id for a in avaliacoes]))) if avaliacoes else []
    por_mat: dict[uuid.UUID, dict[uuid.UUID, Nota]] = defaultdict(dict)
    for n in notas:
        por_mat[n.matricula_id][n.avaliacao_id] = n
    out = {}
    for mid in matricula_ids:
        r = media_periodo([nota_lancada(av, por_mat[mid].get(av.id)) for av in avaliacoes], regra)
        out[mid] = {
            "media": r.media,
            "media_antes_recuperacao": r.media_antes_recuperacao,
            "recuperacao_aplicada": r.recuperacao_aplicada,
            "pendentes": r.pendentes,
        }
    return out


def nome_aluno(a: Aluno) -> str:
    """Nome de exibição: usa o nome social quando existe."""
    return f"{a.nome_social or a.nome} {a.sobrenome}"
