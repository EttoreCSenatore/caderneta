"""Novidades (MO.3): o que mudou em cada versão, filtrado para o público de quem pergunta."""

from fastapi import APIRouter, Depends

from app import versoes
from app.deps import Contexto, com_perfil

router = APIRouter(tags=["novidades"])


@router.get("/novidades")
def novidades(ctx: Contexto = Depends(com_perfil)):
    return {"versao_atual": versoes.versao_atual(), "versoes": versoes.para(versoes.publico_de(ctx.papel))}
