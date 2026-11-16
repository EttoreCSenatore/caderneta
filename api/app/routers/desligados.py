"""Sessão de desligados: dados a apagar ou contas a anonimizar, com aviso antes e adiamento."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from app.audit import registrar
from app.deps import Contexto, equipe, so_admin
from app.desligados import NOME_ANONIMO, data_prevista, purga_aluno
from app.models import Aluno, Escola, SituacaoAluno, UsuarioPerfil

router = APIRouter(tags=["desligados"])


class ConfigIn(BaseModel):
    retencao_aluno_dias: int = Field(ge=30, le=3650)
    retencao_usuario_dias: int = Field(ge=30, le=3650)
    aviso_dias: int = Field(ge=7, le=90)

    @model_validator(mode="after")
    def _aviso_menor(self):
        if self.aviso_dias >= min(self.retencao_aluno_dias, self.retencao_usuario_dias):
            raise ValueError("O aviso precisa ser menor que os prazos de retenção.")
        return self


class AdiarIn(BaseModel):
    dias: int = Field(ge=7, le=730)


class ApagarIn(BaseModel):
    confirmacao: str


def _escola(ctx: Contexto) -> Escola:
    e = ctx.db.get(Escola, ctx.escola_id)
    assert e is not None
    return e


def _item(prevista, avisada_em, concluido_em, hoje) -> dict:
    status = "concluido" if concluido_em else ("avisado" if avisada_em else "aguardando")
    return {
        "status": status,
        "prevista": None if concluido_em else prevista,
        "dias_restantes": None if concluido_em else (prevista - hoje).days,
        "avisado_em": avisada_em,
        "concluido_em": concluido_em,
    }


@router.get("/desligados")
def listar(ctx: Contexto = Depends(equipe)):
    e = _escola(ctx)
    hoje = datetime.now(UTC).date()
    alunos = []
    for a in ctx.db.scalars(
        select(Aluno)
        .where(Aluno.situacao != SituacaoAluno.ativo, Aluno.desligado_em.is_not(None))
        .order_by(Aluno.desligado_em.desc())
    ):
        prevista = data_prevista(a.desligado_em, e.retencao_aluno_desligado_dias, a.purga_adiada_ate)
        alunos.append(
            {
                "id": a.id,
                "nome": f"{a.nome} {a.sobrenome}",
                "situacao": a.situacao,
                "desligado_em": a.desligado_em,
                "adiado": a.purga_adiada_ate is not None,
                **_item(prevista, a.purga_avisada_em, a.purgado_em, hoje),
            }
        )
    usuarios = []
    for p in ctx.db.scalars(
        select(UsuarioPerfil)
        .where(UsuarioPerfil.ativo.is_(False), UsuarioPerfil.desligado_em.is_not(None))
        .order_by(UsuarioPerfil.desligado_em.desc())
    ):
        prevista = data_prevista(p.desligado_em, e.retencao_usuario_desligado_dias, p.anonimizacao_adiada_ate)
        anonimo = p.usuario.anonimizado_em
        usuarios.append(
            {
                "perfil_id": p.id,
                "nome": NOME_ANONIMO if anonimo else p.usuario.nome,
                "papel": p.papel,
                "desligado_em": p.desligado_em,
                "adiado": p.anonimizacao_adiada_ate is not None,
                **_item(prevista, p.anonimizacao_avisada_em, anonimo, hoje),
            }
        )
    return {
        "config": {
            "retencao_aluno_dias": e.retencao_aluno_desligado_dias,
            "retencao_usuario_dias": e.retencao_usuario_desligado_dias,
            "aviso_dias": e.aviso_desligados_dias,
        },
        "alunos": alunos,
        "usuarios": usuarios,
    }


@router.put("/desligados/config")
def salvar_config(body: ConfigIn, ctx: Contexto = Depends(so_admin)):
    e = _escola(ctx)
    e.retencao_aluno_desligado_dias = body.retencao_aluno_dias
    e.retencao_usuario_desligado_dias = body.retencao_usuario_dias
    e.aviso_desligados_dias = body.aviso_dias
    registrar(
        ctx.db, "desligados.config", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, detalhes=body.model_dump()
    )
    return {"ok": True}


@router.post("/desligados/alunos/{aluno_id}/adiar")
def adiar_aluno(aluno_id: uuid.UUID, body: AdiarIn, ctx: Contexto = Depends(so_admin)):
    a = ctx.db.get(Aluno, aluno_id)
    if not a or a.situacao == SituacaoAluno.ativo or a.purgado_em:
        raise HTTPException(404, "Aluno desligado não encontrado.")
    e = _escola(ctx)
    novo = datetime.now(UTC).date() + timedelta(days=body.dias)
    if novo <= data_prevista(a.desligado_em, e.retencao_aluno_desligado_dias, a.purga_adiada_ate):
        raise HTTPException(409, "O apagamento já está previsto para depois dessa data.")
    a.purga_adiada_ate, a.purga_avisada_em = novo, None  # novo prazo, novo aviso
    registrar(
        ctx.db,
        "desligados.adiar_aluno",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="aluno",
        entidade_id=a.id,
        detalhes={"ate": novo.isoformat()},
    )
    return {"prevista": novo}


@router.post("/desligados/usuarios/{perfil_id}/adiar")
def adiar_usuario(perfil_id: uuid.UUID, body: AdiarIn, ctx: Contexto = Depends(so_admin)):
    p = ctx.db.get(UsuarioPerfil, perfil_id)
    if not p or p.ativo or p.desligado_em is None or p.usuario.anonimizado_em:
        raise HTTPException(404, "Usuário desligado não encontrado.")
    e = _escola(ctx)
    novo = datetime.now(UTC).date() + timedelta(days=body.dias)
    if novo <= data_prevista(p.desligado_em, e.retencao_usuario_desligado_dias, p.anonimizacao_adiada_ate):
        raise HTTPException(409, "A anonimização já está prevista para depois dessa data.")
    p.anonimizacao_adiada_ate, p.anonimizacao_avisada_em = novo, None
    registrar(
        ctx.db,
        "desligados.adiar_usuario",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="usuario_perfil",
        entidade_id=p.id,
        detalhes={"ate": novo.isoformat()},
    )
    return {"prevista": novo}


@router.post("/desligados/alunos/{aluno_id}/apagar-agora")
def apagar_agora(aluno_id: uuid.UUID, body: ApagarIn, ctx: Contexto = Depends(so_admin)):
    """Apaga já os dados complementares (por exemplo, a pedido do titular). Irreversível: exige digitar APAGAR."""
    a = ctx.db.get(Aluno, aluno_id)
    if not a or a.situacao == SituacaoAluno.ativo:
        raise HTTPException(404, "Aluno desligado não encontrado.")
    if body.confirmacao != "APAGAR":
        raise HTTPException(422, 'Digite "APAGAR" para confirmar.')
    if a.purgado_em:
        raise HTTPException(409, "Os dados complementares deste aluno já foram apagados.")
    return purga_aluno(ctx.db, a, ctx.usuario.id)
