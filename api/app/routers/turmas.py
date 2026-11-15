"""Turmas e atribuições (professor × turma × disciplina)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.deps import Contexto, com_perfil, ids_alunos_visiveis, so_admin
from app.models import (
    STAFF,
    Aluno,
    AnoLetivo,
    Atribuicao,
    Disciplina,
    Matricula,
    Papel,
    Turma,
    UsuarioPerfil,
)
from app.routers.escola import ano_atual

router = APIRouter(tags=["turmas"])


class TurmaIn(BaseModel):
    nome: str = Field(min_length=1, max_length=40)
    serie: str = Field(min_length=1, max_length=40)
    turno: str = Field(default="manhã", max_length=20)
    ano_letivo_id: uuid.UUID | None = None


class AtribuicaoIn(BaseModel):
    disciplina_id: uuid.UUID
    professor_id: uuid.UUID


def turmas_visiveis(ctx: Contexto):
    """Ids de turmas que o perfil ativo pode ver (None = todas)."""
    if ctx.papel in STAFF:
        return None
    if ctx.papel == Papel.professor:
        return select(Atribuicao.turma_id).where(Atribuicao.professor_id == ctx.usuario.id)
    escopo = ids_alunos_visiveis(ctx)
    return select(Matricula.turma_id).where(Matricula.aluno_id.in_(escopo))


def turma_visivel(ctx: Contexto, turma_id: uuid.UUID) -> Turma:
    q = select(Turma).where(Turma.id == turma_id)
    if (escopo := turmas_visiveis(ctx)) is not None:
        q = q.where(Turma.id.in_(escopo))
    t = ctx.db.scalar(q)
    if not t:
        raise HTTPException(404, "Turma não encontrada.")
    return t


def atribuicao_out(a: Atribuicao) -> dict:
    return {
        "id": a.id,
        "disciplina_id": a.disciplina_id,
        "disciplina": a.disciplina.nome,
        "professor_id": a.professor_id,
        "professor": a.professor.nome,
    }


@router.get("/turmas")
def lista_turmas(ano_letivo_id: uuid.UUID | None = None, ctx: Contexto = Depends(com_perfil)):
    if ano_letivo_id is None:
        ano = ano_atual(ctx)
        if not ano:
            return []
        ano_letivo_id = ano.id
    total = (
        select(Matricula.turma_id, func.count().label("n"))
        .join(Aluno, Aluno.id == Matricula.aluno_id)
        .where(Aluno.situacao == "ativo")
        .group_by(Matricula.turma_id)
        .subquery()
    )
    q = (
        select(Turma, func.coalesce(total.c.n, 0))
        .outerjoin(total, total.c.turma_id == Turma.id)
        .where(Turma.ano_letivo_id == ano_letivo_id)
        .order_by(Turma.serie, Turma.nome)
    )
    if (escopo := turmas_visiveis(ctx)) is not None:
        q = q.where(Turma.id.in_(escopo))
    turmas = ctx.db.execute(q).all()
    atrib = ctx.db.scalars(select(Atribuicao).where(Atribuicao.turma_id.in_([t.id for t, _ in turmas])))
    por_turma: dict[uuid.UUID, list[dict]] = {}
    for a in atrib:
        if ctx.papel == Papel.professor and a.professor_id != ctx.usuario.id:
            continue
        por_turma.setdefault(a.turma_id, []).append(atribuicao_out(a))
    return [
        {
            "id": t.id,
            "nome": t.nome,
            "serie": t.serie,
            "turno": t.turno,
            "alunos": n,
            "atribuicoes": sorted(por_turma.get(t.id, []), key=lambda x: x["disciplina"]),
        }
        for t, n in turmas
    ]


@router.post("/turmas", status_code=201)
def cria_turma(dados: TurmaIn, ctx: Contexto = Depends(so_admin)):
    ano = ctx.db.get(AnoLetivo, dados.ano_letivo_id) if dados.ano_letivo_id else ano_atual(ctx)
    if not ano:
        raise HTTPException(409, "Crie o ano letivo antes das turmas.")
    t = Turma(
        escola_id=ctx.escola_id,
        ano_letivo_id=ano.id,
        nome=dados.nome.strip(),
        serie=dados.serie.strip(),
        turno=dados.turno,
    )
    ctx.db.add(t)
    try:
        with ctx.db.begin_nested():
            ctx.db.flush()
    except IntegrityError:
        raise HTTPException(409, "Já existe uma turma com esse nome neste ano.") from None
    return {"id": t.id, "nome": t.nome, "serie": t.serie, "turno": t.turno}


@router.patch("/turmas/{turma_id}")
def edita_turma(turma_id: uuid.UUID, dados: TurmaIn, ctx: Contexto = Depends(so_admin)):
    t = turma_visivel(ctx, turma_id)
    t.nome, t.serie, t.turno = dados.nome.strip(), dados.serie.strip(), dados.turno
    return {"id": t.id, "nome": t.nome, "serie": t.serie, "turno": t.turno}


@router.get("/turmas/{turma_id}")
def ver_turma(turma_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    t = turma_visivel(ctx, turma_id)
    q = (
        select(Aluno)
        .join(Matricula, Matricula.aluno_id == Aluno.id)
        .where(Matricula.turma_id == t.id, Aluno.situacao == "ativo")
        .order_by(Aluno.nome, Aluno.sobrenome)
    )
    # Responsável e aluno veem a turma, mas só a lista dos próprios alunos.
    if ctx.papel in (Papel.responsavel, Papel.aluno):
        q = q.where(Aluno.id.in_(ids_alunos_visiveis(ctx)))
    alunos = ctx.db.scalars(q)
    atrib = ctx.db.scalars(select(Atribuicao).where(Atribuicao.turma_id == t.id))
    return {
        "id": t.id,
        "nome": t.nome,
        "serie": t.serie,
        "turno": t.turno,
        "alunos": [
            {"id": a.id, "nome": a.nome, "sobrenome": a.sobrenome, "nome_social": a.nome_social, "ra": a.ra}
            for a in alunos
        ],
        "atribuicoes": sorted((atribuicao_out(a) for a in atrib), key=lambda x: x["disciplina"]),
    }


@router.post("/turmas/{turma_id}/atribuicoes", status_code=201)
def atribui(turma_id: uuid.UUID, dados: AtribuicaoIn, ctx: Contexto = Depends(so_admin)):
    t = turma_visivel(ctx, turma_id)
    if not ctx.db.get(Disciplina, dados.disciplina_id):
        raise HTTPException(404, "Disciplina não encontrada.")
    eh_prof = ctx.db.scalar(
        select(UsuarioPerfil.id).where(
            UsuarioPerfil.usuario_id == dados.professor_id,
            UsuarioPerfil.escola_id == ctx.escola_id,
            UsuarioPerfil.papel == Papel.professor,
            UsuarioPerfil.ativo.is_(True),
        )
    )
    if not eh_prof:
        raise HTTPException(422, "Essa pessoa não é professor(a) ativo(a) nesta escola.")
    a = Atribuicao(
        escola_id=ctx.escola_id, turma_id=t.id, disciplina_id=dados.disciplina_id, professor_id=dados.professor_id
    )
    ctx.db.add(a)
    try:
        with ctx.db.begin_nested():
            ctx.db.flush()
    except IntegrityError:
        raise HTTPException(409, "Essa atribuição já existe.") from None
    ctx.db.refresh(a)
    return atribuicao_out(a)


@router.delete("/atribuicoes/{atribuicao_id}", status_code=204)
def remove_atribuicao(atribuicao_id: uuid.UUID, ctx: Contexto = Depends(so_admin)):
    a = ctx.db.get(Atribuicao, atribuicao_id)
    if not a:
        raise HTTPException(404, "Atribuição não encontrada.")
    ctx.db.delete(a)
