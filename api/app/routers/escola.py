"""Escola, ano letivo com períodos, disciplinas e equipe."""

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.deps import Contexto, com_perfil, equipe, so_admin
from app.models import (
    STAFF,
    Aluno,
    AnoLetivo,
    Convite,
    Disciplina,
    Escola,
    Papel,
    Periodo,
    TipoPeriodo,
    Turma,
    UsuarioPerfil,
)

router = APIRouter(tags=["escola"])

QTD_PERIODOS = {TipoPeriodo.bimestre: 4, TipoPeriodo.trimestre: 3, TipoPeriodo.semestre: 2}
NOME_PERIODO = {TipoPeriodo.bimestre: "bimestre", TipoPeriodo.trimestre: "trimestre", TipoPeriodo.semestre: "semestre"}


class EscolaIn(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=200)
    cidade: str | None = Field(default=None, max_length=120)
    uf: str | None = Field(default=None, min_length=2, max_length=2)


class AnoIn(BaseModel):
    ano: int = Field(ge=2000, le=2100)
    tipo_periodo: TipoPeriodo
    inicio: date
    fim: date

    @model_validator(mode="after")
    def datas(self):
        if self.fim <= self.inicio:
            raise ValueError("O fim deve ser depois do início.")
        return self


class DisciplinaIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    ativo: bool = True


class PerfilPatch(BaseModel):
    ativo: bool


def ano_atual(ctx: Contexto) -> AnoLetivo | None:
    return ctx.db.scalar(
        select(AnoLetivo)
        .where(AnoLetivo.escola_id == ctx.escola_id, AnoLetivo.aberto.is_(True))
        .order_by(AnoLetivo.ano.desc())
    )


def divide_periodos(inicio: date, fim: date, n: int) -> list[tuple[date, date]]:
    """Divide o ano em `n` partes de tamanho parecido; a escola ajusta as datas depois se quiser."""
    total = (fim - inicio).days + 1
    partes = []
    for i in range(n):
        a = inicio + timedelta(days=total * i // n)
        b = inicio + timedelta(days=total * (i + 1) // n - 1)
        partes.append((a, b))
    return partes


def ano_out(a: AnoLetivo) -> dict:
    return {
        "id": a.id,
        "ano": a.ano,
        "tipo_periodo": a.tipo_periodo,
        "inicio": a.inicio,
        "fim": a.fim,
        "aberto": a.aberto,
        "periodos": [
            {"id": p.id, "numero": p.numero, "nome": p.nome, "inicio": p.inicio, "fim": p.fim, "fechado": p.fechado}
            for p in a.periodos
        ],
    }


@router.get("/escola")
def ver_escola(ctx: Contexto = Depends(com_perfil)):
    e = ctx.db.get(Escola, ctx.escola_id)
    assert e is not None
    ano = ano_atual(ctx)
    out = {"id": e.id, "nome": e.nome, "cidade": e.cidade, "uf": e.uf, "ano_atual": ano_out(ano) if ano else None}
    if ctx.papel in STAFF:
        out["resumo"] = {
            "alunos": ctx.db.scalar(select(func.count()).select_from(Aluno).where(Aluno.situacao == "ativo")),
            "turmas": ctx.db.scalar(
                select(func.count()).select_from(Turma).where(Turma.ano_letivo_id == (ano.id if ano else None))
            ),
            "professores": ctx.db.scalar(
                select(func.count())
                .select_from(UsuarioPerfil)
                .where(UsuarioPerfil.papel == Papel.professor, UsuarioPerfil.ativo.is_(True))
            ),
            "convites_pendentes": ctx.db.scalar(
                select(func.count())
                .select_from(Convite)
                .where(Convite.aceito_em.is_(None), Convite.revogado.is_(False))
            ),
        }
    return out


@router.patch("/escola")
def edita_escola(dados: EscolaIn, ctx: Contexto = Depends(so_admin)):
    e = ctx.db.get(Escola, ctx.escola_id)
    assert e is not None
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(e, k, v.upper() if k == "uf" and v else v)
    return {"ok": True}


@router.get("/anos-letivos")
def lista_anos(ctx: Contexto = Depends(com_perfil)):
    return [ano_out(a) for a in ctx.db.scalars(select(AnoLetivo).order_by(AnoLetivo.ano.desc()))]


@router.post("/anos-letivos", status_code=201)
def cria_ano(dados: AnoIn, ctx: Contexto = Depends(so_admin)):
    if ctx.db.scalar(select(AnoLetivo.id).where(AnoLetivo.ano == dados.ano)):
        raise HTTPException(409, f"O ano letivo {dados.ano} já existe.")
    ano = AnoLetivo(escola_id=ctx.escola_id, **dados.model_dump())
    ctx.db.add(ano)
    ctx.db.flush()
    for i, (a, b) in enumerate(divide_periodos(dados.inicio, dados.fim, QTD_PERIODOS[dados.tipo_periodo]), 1):
        ctx.db.add(
            Periodo(
                escola_id=ctx.escola_id,
                ano_letivo_id=ano.id,
                numero=i,
                nome=f"{i}º {NOME_PERIODO[dados.tipo_periodo]}",
                inicio=a,
                fim=b,
            )
        )
    ctx.db.flush()
    ctx.db.refresh(ano)
    return ano_out(ano)


@router.get("/disciplinas")
def lista_disciplinas(ctx: Contexto = Depends(com_perfil)):
    return [
        {"id": d.id, "nome": d.nome, "ativo": d.ativo}
        for d in ctx.db.scalars(select(Disciplina).order_by(Disciplina.nome))
    ]


@router.post("/disciplinas", status_code=201)
def cria_disciplina(dados: DisciplinaIn, ctx: Contexto = Depends(so_admin)):
    d = Disciplina(escola_id=ctx.escola_id, nome=dados.nome.strip(), ativo=dados.ativo)
    ctx.db.add(d)
    try:
        with ctx.db.begin_nested():
            ctx.db.flush()
    except IntegrityError:
        raise HTTPException(409, "Já existe uma disciplina com esse nome.") from None
    return {"id": d.id, "nome": d.nome, "ativo": d.ativo}


@router.patch("/disciplinas/{disciplina_id}")
def edita_disciplina(disciplina_id: uuid.UUID, dados: DisciplinaIn, ctx: Contexto = Depends(so_admin)):
    d = ctx.db.get(Disciplina, disciplina_id)
    if not d:
        raise HTTPException(404, "Disciplina não encontrada.")
    d.nome, d.ativo = dados.nome.strip(), dados.ativo
    return {"id": d.id, "nome": d.nome, "ativo": d.ativo}


@router.get("/equipe")
def lista_equipe(ctx: Contexto = Depends(equipe)):
    perfis = ctx.db.scalars(
        select(UsuarioPerfil).where(UsuarioPerfil.papel.in_([Papel.admin, Papel.coordenacao, Papel.professor]))
    )
    return sorted(
        (
            {
                "perfil_id": p.id,
                "usuario_id": p.usuario_id,
                "nome": p.usuario.nome,
                "email": p.usuario.email,
                "papel": p.papel,
                "ativo": p.ativo,
                "totp_ativo": p.usuario.totp_ativo,
            }
            for p in perfis
        ),
        key=lambda x: (x["papel"], x["nome"]),
    )


@router.patch("/equipe/{perfil_id}")
def edita_perfil(perfil_id: uuid.UUID, dados: PerfilPatch, ctx: Contexto = Depends(so_admin)):
    p = ctx.db.get(UsuarioPerfil, perfil_id)
    if not p or p.escola_id != ctx.escola_id:
        raise HTTPException(404, "Perfil não encontrado.")
    if p.id == ctx.perfil.id and not dados.ativo:  # type: ignore[union-attr]
        raise HTTPException(409, "Você não pode desativar o próprio perfil.")
    p.ativo = dados.ativo
    return {"ok": True}
