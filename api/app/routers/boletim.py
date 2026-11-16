"""Boletim do aluno, regra de média da escola e fechamento de período."""

import uuid
from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.audit import registrar
from app.deps import Contexto, aluno_visivel, com_perfil, equipe, ip_de, so_admin
from app.medias import ResultadoAnual, frequencia_pct, media_anual, media_periodo, situacao
from app.models import (
    Arredondamento,
    Atribuicao,
    Aula,
    Avaliacao,
    Frequencia,
    Matricula,
    Nota,
    Papel,
    Periodo,
    Recuperacao,
    RegraMedia,
    StatusNota,
    StatusPresenca,
    TipoMedia,
    Turma,
)
from app.regras import matriculas_da_turma, nota_lancada, regra_do_ano
from app.routers.escola import ano_atual

router = APIRouter(tags=["boletim"])


class RegraIn(BaseModel):
    tipo_media: TipoMedia
    pesos_periodos: list[Decimal] | None = Field(default=None, max_length=6)
    recuperacao: Recuperacao
    arredondamento: Arredondamento
    nota_maxima: Decimal = Field(gt=0, le=1000, decimal_places=2)
    media_aprovacao: Decimal = Field(ge=0, decimal_places=2)
    frequencia_minima: int = Field(ge=0, le=100)


def regra_out(r) -> dict:
    return {
        "tipo_media": r.tipo_media,
        "pesos_periodos": [float(p) for p in r.pesos_periodos] if r.pesos_periodos else None,
        "recuperacao": r.recuperacao,
        "arredondamento": r.arredondamento,
        "nota_maxima": r.nota_maxima,
        "media_aprovacao": r.media_aprovacao,
        "frequencia_minima": r.frequencia_minima,
    }


@router.get("/regra-media")
def ver_regra(ctx: Contexto = Depends(com_perfil)):
    ano = ano_atual(ctx)
    if not ano:
        raise HTTPException(409, "Nenhum ano letivo aberto.")
    return regra_out(regra_do_ano(ctx, ano.id))


@router.put("/regra-media")
def grava_regra(dados: RegraIn, request: Request, ctx: Contexto = Depends(so_admin)):
    ano = ano_atual(ctx)
    if not ano:
        raise HTTPException(409, "Nenhum ano letivo aberto.")
    if dados.media_aprovacao > dados.nota_maxima:
        raise HTTPException(422, "A média de aprovação não pode passar da nota máxima.")
    if dados.pesos_periodos and len(dados.pesos_periodos) != len(ano.periodos):
        raise HTTPException(422, f"Informe um peso para cada um dos {len(ano.periodos)} períodos.")
    r = ctx.db.get(RegraMedia, ano.id)
    antes = regra_out(regra_do_ano(ctx, ano.id))
    if not r:
        r = RegraMedia(ano_letivo_id=ano.id, escola_id=ctx.escola_id)
        ctx.db.add(r)
    for k, v in dados.model_dump().items():
        setattr(r, k, [float(x) for x in v] if k == "pesos_periodos" and v else v)
    registrar(
        ctx.db,
        "regra_media_alterada",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="ano_letivo",
        entidade_id=ano.id,
        detalhes={"antes": {k: str(v) for k, v in antes.items()}, "depois": dados.model_dump(mode="json")},
        ip=ip_de(request),
    )
    ctx.db.flush()
    return regra_out(regra_do_ano(ctx, ano.id))


@router.get("/alunos/{aluno_id}/boletim")
def boletim(aluno_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    aluno = aluno_visivel(ctx, aluno_id)
    ano = ano_atual(ctx)
    m = (
        ctx.db.scalar(select(Matricula).where(Matricula.aluno_id == aluno.id, Matricula.ano_letivo_id == ano.id))
        if ano
        else None
    )
    if not ano or not m:
        return {"ano": ano.ano if ano else None, "turma": None, "periodos": [], "disciplinas": [], "regra": None}
    regra = regra_do_ano(ctx, ano.id)
    familia = ctx.papel in (Papel.responsavel, Papel.aluno)
    periodos = list(ano.periodos)
    ano_fechado = bool(periodos) and all(p.fechado for p in periodos)

    q = select(Atribuicao).where(Atribuicao.turma_id == m.turma_id)
    if ctx.papel == Papel.professor:
        q = q.where(Atribuicao.professor_id == ctx.usuario.id)
    atribs = sorted(ctx.db.scalars(q), key=lambda a: a.disciplina.nome)
    ids = [a.id for a in atribs]

    qa = select(Avaliacao).where(Avaliacao.atribuicao_id.in_(ids))
    if familia:  # família e aluno só veem o que o professor publicou
        qa = qa.where(Avaliacao.publicada.is_(True))
    avs = list(ctx.db.scalars(qa.order_by(Avaliacao.recuperacao, Avaliacao.data.nulls_last(), Avaliacao.criado_em)))
    notas = {
        n.avaliacao_id: n
        for n in ctx.db.scalars(
            select(Nota).where(Nota.matricula_id == m.id, Nota.avaliacao_id.in_([a.id for a in avs]))
        )
    }
    por: dict[tuple, list[Avaliacao]] = defaultdict(list)
    for av in avs:
        por[(av.atribuicao_id, av.periodo_id)].append(av)

    aulas = dict(
        ctx.db.execute(
            select(Aula.atribuicao_id, func.sum(Aula.quantidade))
            .where(Aula.atribuicao_id.in_(ids))
            .group_by(Aula.atribuicao_id)
        ).all()
    )
    faltas: dict[uuid.UUID, dict[str, int]] = defaultdict(lambda: {"falta": 0, "justificada": 0})
    for atrib_id, status, qtd in ctx.db.execute(
        select(Aula.atribuicao_id, Frequencia.status, func.sum(Aula.quantidade))
        .join(Aula, Aula.id == Frequencia.aula_id)
        .where(
            Frequencia.matricula_id == m.id,
            Aula.atribuicao_id.in_(ids),
            Frequencia.status.in_([StatusPresenca.falta, StatusPresenca.justificada]),
        )
        .group_by(Aula.atribuicao_id, Frequencia.status)
    ).all():
        faltas[atrib_id][status.value] = int(qtd)

    disciplinas = []
    total_aulas = total_faltas = 0
    for a in atribs:
        linhas = []
        for p in periodos:
            lista = por.get((a.id, p.id), [])
            r = media_periodo([nota_lancada(av, notas.get(av.id)) for av in lista], regra)
            linhas.append(
                {
                    "periodo_id": p.id,
                    "media": r.media,
                    "recuperacao_aplicada": r.recuperacao_aplicada,
                    "avaliacoes": [
                        {
                            "id": av.id,
                            "nome": av.nome,
                            "tipo": av.tipo,
                            "data": av.data,
                            "peso": av.peso,
                            "nota_maxima": av.nota_maxima,
                            "recuperacao": av.recuperacao,
                            "publicada": av.publicada,
                            "valor": notas[av.id].valor if av.id in notas else None,
                            "status": notas[av.id].status if av.id in notas else StatusNota.normal,
                        }
                        for av in lista
                    ],
                }
            )
        anual = media_anual([x["media"] for x in linhas], regra)
        # A situação final (aprovado/reprovado) só existe com todos os períodos fechados pela escola.
        anual = ResultadoAnual(anual.media, anual.completa and ano_fechado)
        dadas = int(aulas.get(a.id, 0))
        f = faltas[a.id]
        nf = f["falta"] + f["justificada"]
        freq = frequencia_pct(dadas, nf)
        total_aulas += dadas
        total_faltas += nf
        disciplinas.append(
            {
                "atribuicao_id": a.id,
                "disciplina": a.disciplina.nome,
                "professor": a.professor.nome,
                "periodos": linhas,
                "media_anual": anual.media,
                "media_completa": anual.completa,
                "aulas_dadas": dadas,
                "faltas": nf,
                "faltas_justificadas": f["justificada"],
                "frequencia": freq,
                "situacao": situacao(anual, freq, regra),
            }
        )
    return {
        "ano": ano.ano,
        "turma": {"id": m.turma.id, "nome": m.turma.nome, "serie": m.turma.serie},
        "periodos": [{"id": p.id, "nome": p.nome, "fechado": p.fechado} for p in periodos],
        "regra": regra_out(regra),
        "disciplinas": disciplinas,
        "frequencia_geral": frequencia_pct(total_aulas, total_faltas),
        "somente_publicadas": familia,
    }


# --- Fechamento -----------------------------------------------------------------------------------------


class FechamentoIn(BaseModel):
    fechado: bool


@router.post("/periodos/{periodo_id}/fechamento")
def fecha_periodo(periodo_id: uuid.UUID, dados: FechamentoIn, request: Request, ctx: Contexto = Depends(equipe)):
    p = ctx.db.get(Periodo, periodo_id)
    if not p:
        raise HTTPException(404, "Período não encontrado.")
    if not dados.fechado and ctx.papel != Papel.admin:
        raise HTTPException(403, "Só a direção reabre um período.")
    p.fechado = dados.fechado
    registrar(
        ctx.db,
        "periodo_fechado" if dados.fechado else "periodo_reaberto",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="periodo",
        entidade_id=p.id,
        ip=ip_de(request),
    )
    return {"id": p.id, "fechado": p.fechado}


@router.get("/periodos/{periodo_id}/pendencias")
def pendencias(periodo_id: uuid.UUID, ctx: Contexto = Depends(equipe)):
    """Por diário: avaliações, notas em branco e aulas registradas no período."""
    p = ctx.db.get(Periodo, periodo_id)
    if not p:
        raise HTTPException(404, "Período não encontrado.")
    out = []
    for a in ctx.db.scalars(select(Atribuicao)):
        turma = ctx.db.get(Turma, a.turma_id)
        if not turma or turma.ano_letivo_id != p.ano_letivo_id:
            continue
        mids = [m.id for m, _ in matriculas_da_turma(ctx, turma)]
        avs = list(
            ctx.db.scalars(
                select(Avaliacao).where(
                    Avaliacao.atribuicao_id == a.id, Avaliacao.periodo_id == p.id, Avaliacao.recuperacao.is_(False)
                )
            )
        )
        lancadas = (
            ctx.db.scalar(
                select(func.count())
                .select_from(Nota)
                .where(
                    Nota.avaliacao_id.in_([av.id for av in avs]),
                    Nota.matricula_id.in_(mids),
                    (Nota.valor.is_not(None)) | (Nota.status != StatusNota.normal),
                )
            )
            if avs
            else 0
        )
        aulas = ctx.db.scalar(
            select(func.count())
            .select_from(Aula)
            .where(Aula.atribuicao_id == a.id, Aula.data >= p.inicio, Aula.data <= p.fim)
        )
        out.append(
            {
                "atribuicao_id": a.id,
                "turma": turma.nome,
                "disciplina": a.disciplina.nome,
                "professor": a.professor.nome,
                "avaliacoes": len(avs),
                "notas_em_branco": len(avs) * len(mids) - int(lancadas or 0),
                "nao_publicadas": sum(1 for av in avs if not av.publicada),
                "aulas": aulas,
            }
        )
    out.sort(key=lambda x: (x["turma"], x["disciplina"]))
    return out
