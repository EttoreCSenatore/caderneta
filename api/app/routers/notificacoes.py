"""Caixa de notificações do usuário e preferências (e-mail, horário silencioso)."""

import uuid
from datetime import UTC, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, update

from app.deps import Contexto, com_perfil
from app.models import Notificacao

router = APIRouter(tags=["notificacoes"])


class PreferenciasIn(BaseModel):
    email: bool
    silencio_inicio: time
    silencio_fim: time


def _out(n: Notificacao) -> dict:
    return {
        "id": n.id,
        "tipo": n.tipo,
        "titulo": n.titulo,
        "corpo": n.corpo,
        "url": n.url,
        "criado_em": n.criado_em,
        "lida": n.lida_em is not None,
    }


def _minhas(ctx: Contexto):
    return Notificacao.usuario_id == ctx.usuario.id


@router.get("/notificacoes")
def listar(ctx: Contexto = Depends(com_perfil), so_nao_lidas: bool = False):
    q = select(Notificacao).where(_minhas(ctx)).order_by(Notificacao.criado_em.desc()).limit(100)
    if so_nao_lidas:
        q = q.where(Notificacao.lida_em.is_(None))
    return [_out(n) for n in ctx.db.scalars(q)]


@router.get("/notificacoes/contagem")
def contagem(ctx: Contexto = Depends(com_perfil)):
    n = ctx.db.scalar(select(func.count()).select_from(Notificacao).where(_minhas(ctx), Notificacao.lida_em.is_(None)))
    return {"nao_lidas": n}


@router.post("/notificacoes/lidas")
def marcar_todas(ctx: Contexto = Depends(com_perfil)):
    r = ctx.db.execute(
        update(Notificacao).where(_minhas(ctx), Notificacao.lida_em.is_(None)).values(lida_em=datetime.now(UTC))
    )
    return {"marcadas": r.rowcount}


@router.post("/notificacoes/{notificacao_id}/lida")
def marcar(notificacao_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    n = ctx.db.scalar(select(Notificacao).where(Notificacao.id == notificacao_id, _minhas(ctx)))
    if not n:
        raise HTTPException(404, "Notificação não encontrada.")
    n.lida_em = n.lida_em or datetime.now(UTC)
    return _out(n)


@router.get("/notificacoes-preferencias")
def preferencias(ctx: Contexto = Depends(com_perfil)):
    u = ctx.usuario
    return {
        "email": u.notif_email,
        "silencio_inicio": u.silencio_inicio.strftime("%H:%M"),
        "silencio_fim": u.silencio_fim.strftime("%H:%M"),
    }


@router.put("/notificacoes-preferencias")
def salvar_preferencias(body: PreferenciasIn, ctx: Contexto = Depends(com_perfil)):
    u = ctx.usuario
    u.notif_email, u.silencio_inicio, u.silencio_fim = body.email, body.silencio_inicio, body.silencio_fim
    return preferencias(ctx)
