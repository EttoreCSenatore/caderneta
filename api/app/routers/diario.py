"""Diário de classe: avaliações, lançamento de notas e chamada."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from app.alertas import notifica_nota_publicada, verifica_faltas
from app.audit import registrar
from app.calendario import dia_sem_aula
from app.deps import Contexto, equipe_ou_professor, ip_de
from app.medias import frequencia_pct
from app.models import (
    Aula,
    Avaliacao,
    Frequencia,
    Nota,
    Periodo,
    StatusNota,
    StatusPresenca,
    agora,
)
from app.regras import (
    atribuicao_do_diario,
    matriculas_da_turma,
    medias_do_periodo,
    nome_aluno,
    periodo_do_ano,
    pode_escrever,
    regra_do_ano,
)

router = APIRouter(tags=["diario"])

TIPOS = ("prova", "trabalho", "participacao", "simulado", "recuperacao", "outro")


class AvaliacaoIn(BaseModel):
    periodo_id: uuid.UUID
    nome: str = Field(min_length=1, max_length=80)
    tipo: str = Field(default="prova", pattern="^(" + "|".join(TIPOS) + ")$")
    data: date | None = None
    peso: Decimal = Field(default=Decimal(1), ge=0, le=100, decimal_places=2)
    nota_maxima: Decimal = Field(default=Decimal(10), gt=0, le=1000, decimal_places=2)
    recuperacao: bool = False
    justificativa: str | None = Field(default=None, max_length=300)


class NotaIn(BaseModel):
    matricula_id: uuid.UUID
    valor: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    status: StatusNota = StatusNota.normal


class NotasIn(BaseModel):
    notas: list[NotaIn] = Field(max_length=200)
    justificativa: str | None = Field(default=None, max_length=300)


class PublicarIn(BaseModel):
    publicada: bool


class RegistroIn(BaseModel):
    matricula_id: uuid.UUID
    status: StatusPresenca
    justificativa: str | None = Field(default=None, max_length=300)


class AulaIn(BaseModel):
    data: date
    quantidade: int = Field(default=1, ge=1, le=6)
    conteudo: str | None = Field(default=None, max_length=300)
    registros: list[RegistroIn] = Field(default_factory=list, max_length=200)
    justificativa: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def nao_futuro(self):
        if self.data > date.today():
            raise ValueError("Não é possível registrar chamada de uma data futura.")
        return self


def avaliacao_out(a: Avaliacao) -> dict:
    return {
        "id": a.id,
        "periodo_id": a.periodo_id,
        "nome": a.nome,
        "tipo": a.tipo,
        "data": a.data,
        "peso": a.peso,
        "nota_maxima": a.nota_maxima,
        "recuperacao": a.recuperacao,
        "publicada": a.publicada,
    }


def _periodo_padrao(periodos: list[Periodo]) -> Periodo:
    hoje = date.today()
    for p in periodos:
        if p.inicio <= hoje <= p.fim:
            return p
    futuros = [p for p in periodos if p.inicio > hoje]
    return futuros[0] if futuros else periodos[-1]


def _avaliacao_do_diario(ctx: Contexto, avaliacao_id: uuid.UUID):
    av = ctx.db.get(Avaliacao, avaliacao_id)
    if not av:
        raise HTTPException(404, "Avaliação não encontrada.")
    a, turma = atribuicao_do_diario(ctx, av.atribuicao_id)
    return av, a, turma


@router.get("/atribuicoes/{atribuicao_id}/diario")
def diario(atribuicao_id: uuid.UUID, periodo_id: uuid.UUID | None = None, ctx: Contexto = Depends(equipe_ou_professor)):
    a, turma = atribuicao_do_diario(ctx, atribuicao_id)
    periodos = list(
        ctx.db.scalars(select(Periodo).where(Periodo.ano_letivo_id == turma.ano_letivo_id).order_by(Periodo.numero))
    )
    if not periodos:
        raise HTTPException(409, "O ano letivo não tem períodos.")
    periodo = periodo_do_ano(ctx, periodo_id, turma) if periodo_id else _periodo_padrao(periodos)
    regra = regra_do_ano(ctx, turma.ano_letivo_id)
    avaliacoes = list(
        ctx.db.scalars(
            select(Avaliacao)
            .where(Avaliacao.atribuicao_id == a.id, Avaliacao.periodo_id == periodo.id)
            .order_by(Avaliacao.recuperacao, Avaliacao.data.nulls_last(), Avaliacao.criado_em)
        )
    )
    alunos = matriculas_da_turma(ctx, turma)
    mids = [m.id for m, _ in alunos]
    notas: dict[str, dict[str, dict]] = {str(av.id): {} for av in avaliacoes}
    if avaliacoes:
        for n in ctx.db.scalars(select(Nota).where(Nota.avaliacao_id.in_([av.id for av in avaliacoes]))):
            notas[str(n.avaliacao_id)][str(n.matricula_id)] = {"valor": n.valor, "status": n.status}

    aulas = ctx.db.execute(
        select(func.coalesce(func.sum(Aula.quantidade), 0)).where(
            Aula.atribuicao_id == a.id, Aula.data >= periodo.inicio, Aula.data <= periodo.fim
        )
    ).scalar_one()
    faltas = dict(
        ctx.db.execute(
            select(Frequencia.matricula_id, func.sum(Aula.quantidade))
            .join(Aula, Aula.id == Frequencia.aula_id)
            .where(
                Aula.atribuicao_id == a.id,
                Aula.data >= periodo.inicio,
                Aula.data <= periodo.fim,
                Frequencia.status.in_([StatusPresenca.falta, StatusPresenca.justificada]),
            )
            .group_by(Frequencia.matricula_id)
        ).all()
    )
    medias = medias_do_periodo(ctx, avaliacoes, mids, regra)
    return {
        "atribuicao": {
            "id": a.id,
            "disciplina": a.disciplina.nome,
            "professor": a.professor.nome,
            "turma": {"id": turma.id, "nome": turma.nome, "serie": turma.serie},
        },
        "pode_editar": ctx.papel.value == "professor" and a.professor_id == ctx.usuario.id and not periodo.fechado,
        "periodos": [
            {"id": p.id, "nome": p.nome, "inicio": p.inicio, "fim": p.fim, "fechado": p.fechado} for p in periodos
        ],
        "periodo_id": periodo.id,
        "regra": {"nota_maxima": regra.nota_maxima, "media_aprovacao": regra.media_aprovacao},
        "avaliacoes": [avaliacao_out(av) for av in avaliacoes],
        "alunos": [
            {
                "matricula_id": m.id,
                "aluno_id": al.id,
                "nome": nome_aluno(al),
                "faltas": int(faltas.get(m.id, 0)),
                "frequencia": frequencia_pct(int(aulas), int(faltas.get(m.id, 0))),
            }
            for m, al in alunos
        ],
        "aulas_dadas": int(aulas),
        "notas": notas,
        "medias": {str(k): v for k, v in medias.items()},
    }


@router.post("/atribuicoes/{atribuicao_id}/avaliacoes", status_code=201)
def cria_avaliacao(
    atribuicao_id: uuid.UUID, dados: AvaliacaoIn, request: Request, ctx: Contexto = Depends(equipe_ou_professor)
):
    a, turma = atribuicao_do_diario(ctx, atribuicao_id)
    periodo = periodo_do_ano(ctx, dados.periodo_id, turma)
    correcao = pode_escrever(ctx, a, periodo, dados.justificativa)
    if dados.data and not (periodo.inicio <= dados.data <= periodo.fim):
        raise HTTPException(422, f"A data precisa estar dentro do {periodo.nome}.")
    av = Avaliacao(escola_id=ctx.escola_id, atribuicao_id=a.id, **dados.model_dump(exclude={"justificativa"}))
    if av.tipo == "recuperacao":
        av.recuperacao = True
    ctx.db.add(av)
    ctx.db.flush()
    if correcao:
        registrar(
            ctx.db,
            "avaliacao_criada_pela_direcao",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="avaliacao",
            entidade_id=av.id,
            detalhes={"justificativa": dados.justificativa},
            ip=ip_de(request),
        )
    return avaliacao_out(av)


@router.patch("/avaliacoes/{avaliacao_id}")
def edita_avaliacao(
    avaliacao_id: uuid.UUID, dados: AvaliacaoIn, request: Request, ctx: Contexto = Depends(equipe_ou_professor)
):
    av, a, turma = _avaliacao_do_diario(ctx, avaliacao_id)
    atual = ctx.db.get(Periodo, av.periodo_id)
    novo = periodo_do_ano(ctx, dados.periodo_id, turma)
    assert atual is not None
    correcao = pode_escrever(ctx, a, atual, dados.justificativa) | pode_escrever(ctx, a, novo, dados.justificativa)
    if dados.data and not (novo.inicio <= dados.data <= novo.fim):
        raise HTTPException(422, f"A data precisa estar dentro do {novo.nome}.")
    for k, v in dados.model_dump(exclude={"justificativa"}).items():
        setattr(av, k, v)
    if av.tipo == "recuperacao":
        av.recuperacao = True
    if correcao:
        registrar(
            ctx.db,
            "avaliacao_corrigida",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="avaliacao",
            entidade_id=av.id,
            detalhes={"justificativa": dados.justificativa},
            ip=ip_de(request),
        )
    return avaliacao_out(av)


@router.delete("/avaliacoes/{avaliacao_id}", status_code=204)
def remove_avaliacao(
    avaliacao_id: uuid.UUID,
    request: Request,
    justificativa: str | None = None,
    ctx: Contexto = Depends(equipe_ou_professor),
):
    av, a, _ = _avaliacao_do_diario(ctx, avaliacao_id)
    periodo = ctx.db.get(Periodo, av.periodo_id)
    assert periodo is not None
    pode_escrever(ctx, a, periodo, justificativa)
    lancadas = ctx.db.scalar(select(func.count()).select_from(Nota).where(Nota.avaliacao_id == av.id))
    registrar(
        ctx.db,
        "avaliacao_removida",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="avaliacao",
        entidade_id=av.id,
        detalhes={"nome": av.nome, "notas_lancadas": lancadas, "justificativa": justificativa},
        ip=ip_de(request),
    )
    ctx.db.delete(av)


@router.put("/avaliacoes/{avaliacao_id}/notas")
def lanca_notas(
    avaliacao_id: uuid.UUID, dados: NotasIn, request: Request, ctx: Contexto = Depends(equipe_ou_professor)
):
    av, a, turma = _avaliacao_do_diario(ctx, avaliacao_id)
    periodo = ctx.db.get(Periodo, av.periodo_id)
    assert periodo is not None
    correcao = pode_escrever(ctx, a, periodo, dados.justificativa)
    validas = {m.id for m, _ in matriculas_da_turma(ctx, turma)}
    existentes = {n.matricula_id: n for n in ctx.db.scalars(select(Nota).where(Nota.avaliacao_id == av.id))}
    mudancas = []
    for item in dados.notas:
        if item.matricula_id not in validas:
            raise HTTPException(422, "Aluno não pertence a esta turma.")
        if item.valor is not None and item.valor > av.nota_maxima:
            raise HTTPException(422, f"A nota máxima desta avaliação é {av.nota_maxima}.")
        valor = None if item.status != StatusNota.normal or item.valor is None else item.valor
        n = existentes.get(item.matricula_id)
        antes = (str(n.valor) if n and n.valor is not None else None, n.status if n else None)
        if n is None:
            n = Nota(escola_id=ctx.escola_id, avaliacao_id=av.id, matricula_id=item.matricula_id)
            ctx.db.add(n)
        n.valor = valor  # type: ignore[assignment]
        n.status = item.status
        n.atualizado_por = ctx.usuario.id
        n.atualizado_em = agora()
        mudancas.append(
            {
                "matricula_id": str(item.matricula_id),
                "antes": antes[0],
                "depois": None if valor is None else f"{valor:.2f}",
            }
        )
    if correcao:
        registrar(
            ctx.db,
            "notas_corrigidas",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="avaliacao",
            entidade_id=av.id,
            detalhes={"justificativa": dados.justificativa, "mudancas": mudancas, "periodo_fechado": periodo.fechado},
            ip=ip_de(request),
        )
    ctx.db.flush()
    avaliacoes = list(
        ctx.db.scalars(select(Avaliacao).where(Avaliacao.atribuicao_id == a.id, Avaliacao.periodo_id == periodo.id))
    )
    medias = medias_do_periodo(
        ctx, avaliacoes, [n.matricula_id for n in dados.notas], regra_do_ano(ctx, turma.ano_letivo_id)
    )
    return {"medias": {str(k): v for k, v in medias.items()}}


@router.post("/avaliacoes/{avaliacao_id}/publicar")
def publica(avaliacao_id: uuid.UUID, dados: PublicarIn, ctx: Contexto = Depends(equipe_ou_professor)):
    av, a, _ = _avaliacao_do_diario(ctx, avaliacao_id)
    periodo = ctx.db.get(Periodo, av.periodo_id)
    assert periodo is not None
    if not (ctx.papel.value == "professor" and a.professor_id == ctx.usuario.id) and ctx.papel.value != "admin":
        raise HTTPException(403, "Sem permissão para esta ação.")
    if periodo.fechado and ctx.papel.value != "admin":
        raise HTTPException(409, f"O {periodo.nome} está fechado. Peça à direção para corrigir.")
    era_publicada = av.publicada
    av.publicada = dados.publicada
    if dados.publicada and not era_publicada and not av.notificada_em:
        av.notificada_em = datetime.now(UTC)
        ctx.db.flush()
        notifica_nota_publicada(ctx.db, ctx.escola_id, av, a.disciplina.nome)
    return avaliacao_out(av)


# --- Chamada ---------------------------------------------------------------------------------------------


def _periodo_da_data(ctx: Contexto, turma, data: date) -> Periodo:
    p = ctx.db.scalar(
        select(Periodo).where(Periodo.ano_letivo_id == turma.ano_letivo_id, Periodo.inicio <= data, Periodo.fim >= data)
    )
    if not p:
        raise HTTPException(422, "A data não está em nenhum período do ano letivo.")
    return p


def _sem_aula(ctx: Contexto, turma, data: date) -> None:
    ev = dia_sem_aula(ctx.db, ctx.escola_id, turma.id, data)
    if ev:
        raise HTTPException(409, f"Dia sem aula: {ev.titulo}. A chamada não pode ser registrada nesta data.")


def _grava_chamada(ctx: Contexto, aula: Aula, turma, registros: list[RegistroIn]) -> None:
    validas = {m.id for m, _ in matriculas_da_turma(ctx, turma)}
    atuais = {f.matricula_id: f for f in ctx.db.scalars(select(Frequencia).where(Frequencia.aula_id == aula.id))}
    vistos = set()
    for r in registros:
        if r.matricula_id not in validas:
            raise HTTPException(422, "Aluno não pertence a esta turma.")
        vistos.add(r.matricula_id)
        f = atuais.get(r.matricula_id)
        if r.status == StatusPresenca.presente:
            if f:
                ctx.db.delete(f)
            continue
        if not f:
            f = Frequencia(escola_id=ctx.escola_id, aula_id=aula.id, matricula_id=r.matricula_id, status=r.status)
            ctx.db.add(f)
        f.status = r.status
        f.justificativa = r.justificativa if r.status == StatusPresenca.justificada else None
    for mid, f in atuais.items():  # quem não veio na lista volta a ser presente
        if mid not in vistos:
            ctx.db.delete(f)


def _aula_out(ctx: Contexto, aula: Aula) -> dict:
    regs = list(ctx.db.scalars(select(Frequencia).where(Frequencia.aula_id == aula.id)))
    return {
        "id": aula.id,
        "data": aula.data,
        "quantidade": aula.quantidade,
        "conteudo": aula.conteudo,
        "registros": [
            {"matricula_id": f.matricula_id, "status": f.status, "justificativa": f.justificativa} for f in regs
        ],
    }


@router.get("/atribuicoes/{atribuicao_id}/aulas")
def lista_aulas(atribuicao_id: uuid.UUID, periodo_id: uuid.UUID, ctx: Contexto = Depends(equipe_ou_professor)):
    a, turma = atribuicao_do_diario(ctx, atribuicao_id)
    p = periodo_do_ano(ctx, periodo_id, turma)
    aulas = ctx.db.scalars(
        select(Aula)
        .where(Aula.atribuicao_id == a.id, Aula.data >= p.inicio, Aula.data <= p.fim)
        .order_by(Aula.data.desc(), Aula.criado_em.desc())
    )
    return [_aula_out(ctx, au) for au in aulas]


@router.post("/atribuicoes/{atribuicao_id}/aulas", status_code=201)
def registra_aula(
    atribuicao_id: uuid.UUID, dados: AulaIn, request: Request, ctx: Contexto = Depends(equipe_ou_professor)
):
    a, turma = atribuicao_do_diario(ctx, atribuicao_id)
    periodo = _periodo_da_data(ctx, turma, dados.data)
    _sem_aula(ctx, turma, dados.data)
    correcao = pode_escrever(ctx, a, periodo, dados.justificativa)
    aula = Aula(
        escola_id=ctx.escola_id,
        atribuicao_id=a.id,
        data=dados.data,
        quantidade=dados.quantidade,
        conteudo=dados.conteudo,
    )
    ctx.db.add(aula)
    ctx.db.flush()
    _grava_chamada(ctx, aula, turma, dados.registros)
    ctx.db.flush()
    verifica_faltas(ctx.db, ctx.escola_id, [r.matricula_id for r in dados.registros])
    if correcao:
        registrar(
            ctx.db,
            "chamada_corrigida",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="aula",
            entidade_id=aula.id,
            detalhes={"justificativa": dados.justificativa},
            ip=ip_de(request),
        )
    ctx.db.flush()
    return _aula_out(ctx, aula)


@router.put("/aulas/{aula_id}")
def edita_aula(aula_id: uuid.UUID, dados: AulaIn, request: Request, ctx: Contexto = Depends(equipe_ou_professor)):
    aula = ctx.db.get(Aula, aula_id)
    if not aula:
        raise HTTPException(404, "Aula não encontrada.")
    a, turma = atribuicao_do_diario(ctx, aula.atribuicao_id)
    correcao = pode_escrever(ctx, a, _periodo_da_data(ctx, turma, aula.data), dados.justificativa)
    correcao |= pode_escrever(ctx, a, _periodo_da_data(ctx, turma, dados.data), dados.justificativa)
    if dados.data != aula.data:
        _sem_aula(ctx, turma, dados.data)
    aula.data, aula.quantidade, aula.conteudo = dados.data, dados.quantidade, dados.conteudo
    _grava_chamada(ctx, aula, turma, dados.registros)
    ctx.db.flush()
    verifica_faltas(ctx.db, ctx.escola_id, [r.matricula_id for r in dados.registros])
    if correcao:
        registrar(
            ctx.db,
            "chamada_corrigida",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="aula",
            entidade_id=aula.id,
            detalhes={"justificativa": dados.justificativa},
            ip=ip_de(request),
        )
    ctx.db.flush()
    return _aula_out(ctx, aula)


@router.delete("/aulas/{aula_id}", status_code=204)
def remove_aula(aula_id: uuid.UUID, justificativa: str | None = None, ctx: Contexto = Depends(equipe_ou_professor)):
    aula = ctx.db.get(Aula, aula_id)
    if not aula:
        raise HTTPException(404, "Aula não encontrada.")
    a, turma = atribuicao_do_diario(ctx, aula.atribuicao_id)
    pode_escrever(ctx, a, _periodo_da_data(ctx, turma, aula.data), justificativa)
    ctx.db.delete(aula)
