"""Situação da instalação para a direção (MO.4): backups, teste de restauração, disco e memória."""

from fastapi import APIRouter, Depends

from app import operacao
from app.deps import Contexto, so_admin

router = APIRouter(tags=["operacao"])


@router.get("/operacao")
def situacao(ctx: Contexto = Depends(so_admin)):
    return operacao.situacao(ctx.db)
