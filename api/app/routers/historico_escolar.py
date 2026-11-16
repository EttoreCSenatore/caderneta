"""Histórico escolar em PDF: emissão pela equipe (registrada) e conferência pública do código."""

import re
import secrets
import unicodedata
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.audit import registrar
from app.config import get_settings
from app.db import get_db
from app.deps import Contexto, aluno_visivel, equipe
from app.historico_escolar import dados_do_historico, renderiza, resumo_sha256
from app.models import Escola, HistoricoEmitido
from app.routers.historico import anos_do_aluno

router = APIRouter(tags=["historico-escolar"])


def novo_codigo() -> str:
    h = secrets.token_hex(6).upper()
    return f"{h[:4]}-{h[4:8]}-{h[8:]}"


def normaliza_codigo(c: str) -> str | None:
    limpo = re.sub(r"[^0-9A-Fa-f]", "", c).upper()
    return f"{limpo[:4]}-{limpo[4:8]}-{limpo[8:]}" if len(limpo) == 12 else None


def _nome_arquivo(nome: str) -> str:
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower() or "aluno"


@router.post("/alunos/{aluno_id}/historico-escolar")
def emitir(aluno_id: uuid.UUID, ctx: Contexto = Depends(equipe)):
    """Gera o PDF a partir dos dados atuais. Cada emissão é registrada com quem emitiu e um código de conferência."""
    aluno = aluno_visivel(ctx, aluno_id)
    escola = ctx.db.get(Escola, ctx.escola_id)
    assert escola is not None
    dados = dados_do_historico(escola, aluno, anos_do_aluno(ctx, aluno, detalhado=True))
    codigo = novo_codigo()
    ctx.db.add(
        HistoricoEmitido(
            escola_id=ctx.escola_id,
            aluno_id=aluno.id,
            emitido_por=ctx.usuario.id,
            codigo=codigo,
            resumo_sha256=resumo_sha256(dados),
        )
    )
    registrar(
        ctx.db,
        "historico.emitir",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="aluno",
        entidade_id=aluno.id,
        detalhes={"codigo": codigo},
    )
    base = get_settings().public_url.rstrip("/")
    pdf = renderiza(dados, codigo=codigo, emitido_por=ctx.usuario.nome, url_verificacao=f"{base}/verificar/{codigo}")
    nome = _nome_arquivo(f"{aluno.nome} {aluno.sobrenome}")
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="historico-escolar-{nome}.pdf"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/alunos/{aluno_id}/historicos-emitidos")
def emitidos(aluno_id: uuid.UUID, ctx: Contexto = Depends(equipe)):
    aluno = aluno_visivel(ctx, aluno_id)
    q = (
        select(HistoricoEmitido)
        .where(HistoricoEmitido.aluno_id == aluno.id)
        .order_by(HistoricoEmitido.emitido_em.desc())
    )
    return [
        {
            "codigo": h.codigo,
            "emitido_em": h.emitido_em,
            "emitido_por": h.emissor.nome if h.emissor else None,
        }
        for h in ctx.db.scalars(q)
    ]


@router.get("/historico/verificar/{codigo}")
def verificar(codigo: str, db: Session = Depends(get_db, scope="function")):
    """Público (quem confere não tem login): confirma o código e mostra só o mínimo para reconhecer o documento."""
    c = normaliza_codigo(codigo)
    linha = None
    if c:
        sql = text("SELECT escola, emitido_em, iniciais FROM verificar_historico(:c)")
        linha = db.execute(sql, {"c": c}).first()
    if not linha:
        raise HTTPException(404, "Código não encontrado.")
    return {"valido": True, "escola": linha.escola, "emitido_em": linha.emitido_em, "aluno": linha.iniciais}
