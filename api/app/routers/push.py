"""Inscrição de aparelhos para push (sem conteúdo). Só adultos; contas de aluno (menores) não recebem."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text

from app import push
from app.audit import registrar
from app.deps import Contexto, com_perfil
from app.models import Papel, PushInscricao, UsuarioPerfil

router = APIRouter(tags=["push"])


class InscricaoIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000)


def _adulto(ctx: Contexto) -> bool:
    papeis = set(ctx.db.scalars(select(UsuarioPerfil.papel).where(UsuarioPerfil.usuario_id == ctx.usuario.id)))
    return bool(papeis - {Papel.aluno})


@router.get("/push/config")
def config(ctx: Contexto = Depends(com_perfil)):
    return {
        "ativo": push.ativo(),
        "chave_publica": push.chave_publica() if push.ativo() else None,
        "permitido": _adulto(ctx),
    }


@router.get("/push/aparelhos")
def aparelhos(ctx: Contexto = Depends(com_perfil)):
    n = ctx.db.scalar(select(func.count()).select_from(PushInscricao).where(PushInscricao.usuario_id == ctx.usuario.id))
    return {"aparelhos": n}


@router.post("/push/inscricoes", status_code=201)
def inscrever(body: InscricaoIn, ctx: Contexto = Depends(com_perfil)):
    if not push.ativo():
        raise HTTPException(409, "O push não está ativado neste servidor.")
    if not _adulto(ctx):
        raise HTTPException(403, "Contas de aluno não recebem push. Use as notificações dentro do app.")
    if not push.endpoint_valido(body.endpoint):
        raise HTTPException(422, "Endereço de push não aceito.")
    agora = datetime.now(UTC)
    atual = ctx.db.scalar(select(PushInscricao).where(PushInscricao.endpoint == body.endpoint))
    if atual:
        atual.ultimo_uso_em = agora
    else:
        # se o aparelho já era de outra pessoa (mesmo navegador), a inscrição antiga some
        ctx.db.execute(text("SELECT push_liberar_endpoint(:e)"), {"e": body.endpoint})
        ctx.db.add(PushInscricao(usuario_id=ctx.usuario.id, endpoint=body.endpoint))
        registrar(
            ctx.db, "push.inscrever", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, entidade="push_inscricao"
        )
    return {"ok": True}


@router.post("/push/cancelar", status_code=204)
def cancelar(body: InscricaoIn, ctx: Contexto = Depends(com_perfil)):
    """Cancela este aparelho (também chamado ao sair do app)."""
    r = ctx.db.execute(
        PushInscricao.__table__.delete().where(
            PushInscricao.endpoint == body.endpoint, PushInscricao.usuario_id == ctx.usuario.id
        )
    )
    if r.rowcount:
        registrar(
            ctx.db, "push.cancelar", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, entidade="push_inscricao"
        )
