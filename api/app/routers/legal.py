"""Política de privacidade e termos de uso: texto público e confirmação (ciência) por versão."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.audit import registrar
from app.deps import Contexto, ip_de, sessao_parcial
from app.legal import DOCS, carrega
from app.models import AceiteLegal

router = APIRouter(tags=["legal"])


class AceiteIn(BaseModel):
    doc: Literal["privacidade", "termos"]
    versao: str


class AceitesIn(BaseModel):
    aceites: list[AceiteIn]


@router.get("/legal/pendentes")
def pendentes(ctx: Contexto = Depends(sessao_parcial)):
    """Textos cuja versão atual esta pessoa ainda não confirmou."""
    feitos = {
        (a.doc, a.versao) for a in ctx.db.scalars(select(AceiteLegal).where(AceiteLegal.usuario_id == ctx.usuario.id))
    }
    saida = []
    for d in DOCS:
        c = carrega(d)
        if (d, c["versao"]) not in feitos:
            saida.append({"doc": d, "versao": c["versao"], "titulo": c["titulo"], "status": c["status"]})
    return saida


@router.post("/legal/aceitar", status_code=204)
def aceitar(dados: AceitesIn, request: Request, ctx: Contexto = Depends(sessao_parcial)):
    for a in dados.aceites:
        if a.versao != carrega(a.doc)["versao"]:
            raise HTTPException(409, "O texto mudou. Recarregue a página e leia a versão atual.")
    existentes = {
        (x.doc, x.versao) for x in ctx.db.scalars(select(AceiteLegal).where(AceiteLegal.usuario_id == ctx.usuario.id))
    }
    for a in dados.aceites:
        if (a.doc, a.versao) in existentes:
            continue
        ctx.db.add(AceiteLegal(usuario_id=ctx.usuario.id, doc=a.doc, versao=a.versao))
        registrar(
            ctx.db,
            "legal.aceite",
            escola_id=None,
            usuario_id=ctx.usuario.id,
            detalhes={"doc": a.doc, "versao": a.versao},
            ip=ip_de(request),
        )


@router.get("/legal/{doc}")
def texto(doc: str):
    """Público: qualquer pessoa pode ler antes de entrar."""
    if doc not in DOCS:
        raise HTTPException(404, "Documento não encontrado.")
    return carrega(doc)
