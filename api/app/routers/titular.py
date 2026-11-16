"""Direitos dos titulares (LGPD art. 18 e 19): baixar os próprios dados e fazer pedidos à escola.

Fluxo: a pessoa baixa os próprios dados na hora (acesso simplificado, art. 19, I) ou abre um pedido (correção,
eliminação, portabilidade, informação). A direção responde em até 15 dias corridos (art. 19, II) e a resposta fica
registrada. Pedidos recebidos por outros canais (balcão, e-mail, telefone) são cadastrados pela direção com a data
original de recebimento: o prazo conta a partir dela, não de quando alguém digitou.
"""

import json
import re
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.audit import registrar
from app.deps import Contexto, aluno_visivel, com_perfil, equipe, ip_de, so_admin
from app.models import STAFF, Aluno, Papel, PedidoTitular, Usuario
from app.notificacoes import equipe_da_escola, notificar
from app.regras import nome_aluno
from app.routers.auth import bloqueado, registra_falha
from app.security import verifica_senha
from app.titular import exporta_aluno, exporta_usuario, pacote

router = APIRouter(tags=["titular"])

PRAZO_DIAS = 15
TIPOS = Literal["acesso", "correcao", "eliminacao", "portabilidade", "informacao", "revogacao", "outro"]
FINAIS = {"atendido", "em_parte", "negado"}


class ExportarIn(BaseModel):
    senha: str = Field(max_length=200)
    aluno_id: uuid.UUID | None = None


class PedidoIn(BaseModel):
    tipo: TIPOS
    descricao: str = Field(min_length=10, max_length=2000)
    aluno_id: uuid.UUID | None = None


class RegistroIn(PedidoIn):
    titular_nome: str = Field(min_length=2, max_length=200)
    titular_contato: str | None = Field(default=None, max_length=200)
    canal: Literal["presencial", "email", "telefone", "outro"]
    recebido_em: date | None = None


class RespostaIn(BaseModel):
    status: Literal["em_analise", "atendido", "em_parte", "negado"]
    resposta: str = Field(min_length=10, max_length=4000)


def _pedido_out(p: PedidoTitular, agora: datetime | None = None, equipe_vendo: bool = False) -> dict:
    agora = agora or datetime.now(UTC)
    aberto = p.status not in FINAIS
    dias = (p.prazo_em - agora).total_seconds() / 86400
    out = {
        "id": p.id,
        "tipo": p.tipo,
        "canal": p.canal,
        "descricao": p.descricao,
        "status": p.status,
        "recebido_em": p.recebido_em,
        "prazo_em": p.prazo_em,
        "vencido": aberto and dias < 0,
        "dias_restantes": int(dias // 1) if aberto else None,
        "resposta": p.resposta,
        "respondido_em": p.respondido_em,
        "aluno": nome_aluno(p.aluno) if p.aluno else None,
        "aluno_id": p.aluno_id,
    }
    if equipe_vendo:
        out["solicitante"] = (
            {"nome": p.solicitante.nome, "email": p.solicitante.email} if p.solicitante else None
        ) or ({"nome": p.titular_nome, "email": p.titular_contato} if p.titular_nome else None)
    return out


def _download(dados: dict, nome: str) -> Response:
    corpo = json.dumps(dados, ensure_ascii=False, indent=2, default=str)
    seguro = re.sub(r"[^A-Za-z0-9_-]+", "-", nome)[:60] or "dados"
    return Response(
        corpo,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="caderneta-{seguro}.json"', "Cache-Control": "no-store"},
    )


# --- Titular logado --------------------------------------------------------------------------------------


@router.post("/meus-dados/exportar")
def exportar(dados: ExportarIn, request: Request, ctx: Contexto = Depends(com_perfil)):
    """Baixa os próprios dados (ou os do filho, para o responsável). Pede a senha de novo: é dado pessoal sensível."""
    u = ctx.usuario
    if bloqueado(u):
        return JSONResponse({"detail": "Muitas tentativas. Tente de novo em alguns minutos."}, 429)
    if not verifica_senha(u.senha_hash, dados.senha):
        registra_falha(ctx.db, u)
        return JSONResponse({"detail": "Senha incorreta."}, 400)
    if dados.aluno_id:
        if ctx.papel not in (Papel.responsavel, Papel.aluno):
            raise HTTPException(403, "Sem permissão para esta ação.")
        a = aluno_visivel(ctx, dados.aluno_id)
        conteudo = pacote(f"Dados de {nome_aluno(a)}", exporta_aluno(ctx.db, a, ctx.papel, u.id))
        alvo = ("aluno", a.id)
        nome = nome_aluno(a)
    else:
        conteudo = pacote(f"Dados de {u.nome}", exporta_usuario(ctx.db, u))
        alvo, nome = ("usuario", u.id), u.nome
    registrar(
        ctx.db,
        "titular.exportou",
        escola_id=ctx.escola_id,
        usuario_id=u.id,
        entidade=alvo[0],
        entidade_id=alvo[1],
        ip=ip_de(request),
    )
    return _download(conteudo, nome)


@router.get("/meus-dados/pedidos")
def meus_pedidos(ctx: Contexto = Depends(com_perfil)):
    q = (
        select(PedidoTitular)
        .where(PedidoTitular.solicitante_id == ctx.usuario.id)
        .order_by(PedidoTitular.criado_em.desc())
    )
    return [_pedido_out(p) for p in ctx.db.scalars(q)]


@router.post("/meus-dados/pedidos", status_code=201)
def novo_pedido(dados: PedidoIn, request: Request, ctx: Contexto = Depends(com_perfil)):
    aluno: Aluno | None = None
    if dados.aluno_id:
        if ctx.papel not in (Papel.responsavel, Papel.aluno):
            raise HTTPException(403, "Sem permissão para esta ação.")
        aluno = aluno_visivel(ctx, dados.aluno_id)
    agora = datetime.now(UTC)
    p = PedidoTitular(
        escola_id=ctx.escola_id,
        solicitante_id=ctx.usuario.id,
        aluno_id=aluno.id if aluno else None,
        tipo=dados.tipo,
        canal="app",
        descricao=dados.descricao,
        status="aberto",
        recebido_em=agora,
        prazo_em=agora + timedelta(days=PRAZO_DIAS),
    )
    ctx.db.add(p)
    ctx.db.flush()
    registrar(
        ctx.db,
        "titular.pedido",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="pedido_titular",
        entidade_id=p.id,
        detalhes={"tipo": p.tipo},
        ip=ip_de(request),
    )
    notificar(
        ctx.db,
        escola_id=ctx.escola_id,
        usuarios=equipe_da_escola(ctx.db, ctx.escola_id),
        tipo="titular",
        titulo="Novo pedido de titular de dados",
        corpo="Prazo de resposta: 15 dias.",
        url="/pedidos-titulares",
        excluir=ctx.usuario.id,
    )
    ctx.db.refresh(p)
    return _pedido_out(p)


# --- Direção ---------------------------------------------------------------------------------------------


@router.get("/pedidos-titulares")
def lista_pedidos(ctx: Contexto = Depends(equipe)):
    agora = datetime.now(UTC)
    itens = list(ctx.db.scalars(select(PedidoTitular)))
    itens.sort(key=lambda p: (p.status in FINAIS, p.prazo_em))
    return [_pedido_out(p, agora, equipe_vendo=True) for p in itens]


@router.get("/pedidos-titulares/contagem")
def contagem(ctx: Contexto = Depends(equipe)):
    agora = datetime.now(UTC)
    abertos = [p for p in ctx.db.scalars(select(PedidoTitular)) if p.status not in FINAIS]
    return {"abertos": len(abertos), "vencidos": sum(1 for p in abertos if p.prazo_em < agora)}


@router.post("/pedidos-titulares", status_code=201)
def registra_pedido(dados: RegistroIn, request: Request, ctx: Contexto = Depends(so_admin)):
    """Pedido recebido fora do app: o prazo conta da data em que a escola recebeu."""
    if dados.aluno_id:
        aluno_visivel(ctx, dados.aluno_id)
    hoje = datetime.now(UTC)
    recebido = datetime.combine(dados.recebido_em, time(12, 0), UTC) if dados.recebido_em else hoje
    if recebido > hoje:
        raise HTTPException(422, "A data de recebimento não pode ser futura.")
    p = PedidoTitular(
        escola_id=ctx.escola_id,
        aluno_id=dados.aluno_id,
        titular_nome=dados.titular_nome,
        titular_contato=dados.titular_contato,
        tipo=dados.tipo,
        canal=dados.canal,
        descricao=dados.descricao,
        status="aberto",
        recebido_em=recebido,
        prazo_em=recebido + timedelta(days=PRAZO_DIAS),
    )
    ctx.db.add(p)
    ctx.db.flush()
    registrar(
        ctx.db,
        "titular.pedido_registrado",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="pedido_titular",
        entidade_id=p.id,
        detalhes={"tipo": p.tipo, "canal": p.canal},
        ip=ip_de(request),
    )
    ctx.db.refresh(p)
    return _pedido_out(p, equipe_vendo=True)


def _pedido(ctx: Contexto, pedido_id: uuid.UUID) -> PedidoTitular:
    p = ctx.db.get(PedidoTitular, pedido_id)
    if not p:
        raise HTTPException(404, "Pedido não encontrado.")
    return p


@router.post("/pedidos-titulares/{pedido_id}/responder")
def responde(pedido_id: uuid.UUID, dados: RespostaIn, request: Request, ctx: Contexto = Depends(so_admin)):
    p = _pedido(ctx, pedido_id)
    if p.status in FINAIS:
        raise HTTPException(409, "Este pedido já foi respondido.")
    p.status, p.resposta = dados.status, dados.resposta
    if dados.status in FINAIS:
        p.respondido_em, p.respondido_por = datetime.now(UTC), ctx.usuario.id
    registrar(
        ctx.db,
        "titular.respondido",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="pedido_titular",
        entidade_id=p.id,
        detalhes={"status": dados.status, "tipo": p.tipo},
        ip=ip_de(request),
    )
    if p.solicitante_id:
        notificar(
            ctx.db,
            escola_id=ctx.escola_id,
            usuarios=[p.solicitante_id],
            tipo="titular",
            titulo="Seu pedido sobre dados pessoais foi respondido",
            corpo="Abra Meus dados para ver a resposta.",
            url="/meus-dados",
        )
    return _pedido_out(p, equipe_vendo=True)


@router.post("/pedidos-titulares/{pedido_id}/exportar")
def exporta_do_pedido(pedido_id: uuid.UUID, request: Request, ctx: Contexto = Depends(so_admin)):
    """A direção gera o arquivo de dados do titular para entregar a quem pediu (acesso ou portabilidade)."""
    p = _pedido(ctx, pedido_id)
    if p.aluno_id:
        a = ctx.db.get(Aluno, p.aluno_id)
        assert a is not None
        conteudo = pacote(f"Dados de {nome_aluno(a)}", exporta_aluno(ctx.db, a, Papel.responsavel, p.solicitante_id))
        alvo, nome = ("aluno", a.id), nome_aluno(a)
    elif p.solicitante_id:
        u = ctx.db.get(Usuario, p.solicitante_id)
        assert u is not None
        conteudo = pacote(f"Dados de {u.nome}", exporta_usuario(ctx.db, u))
        alvo, nome = ("usuario", u.id), u.nome
    else:
        raise HTTPException(
            409, "Este pedido não está ligado a uma conta nem a um aluno. Atenda pelos dados do cadastro."
        )
    registrar(
        ctx.db,
        "titular.exportou_para_titular",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade=alvo[0],
        entidade_id=alvo[1],
        detalhes={"pedido": str(p.id)},
        ip=ip_de(request),
    )
    return _download(conteudo, nome)


_ = STAFF  # (a checagem de papel está nas dependências)
