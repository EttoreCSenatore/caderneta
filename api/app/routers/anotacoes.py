"""Anotações sobre o aluno: pedagógica, ocorrência, elogio e reservada, com versionamento e visibilidade por tipo.

Quem vê o quê:
- direção e coordenação: tudo, inclusive as reservadas (cada leitura de reservada fica na auditoria);
- professor do aluno no ano aberto: pedagógicas e elogios de **todos os anos** (passar o bastão) e as próprias
  ocorrências;
- responsável (vínculo sem restrição): elogios e as ocorrências marcadas como visíveis;
- a conta do aluno não vê anotações.
Editar cria uma versão nova (a anterior permanece); remover só marca como removida e o worker elimina depois de 30 dias.
"""

import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.audit import registrar
from app.deps import Contexto, aluno_visivel, com_perfil
from app.models import (
    STAFF,
    Aluno,
    Anotacao,
    AnotacaoVersao,
    Papel,
    TipoAnotacao,
)
from app.notificacoes import equipe_da_escola, familia_dos_alunos, notificar
from app.routers.escola import ano_atual

router = APIRouter(tags=["anotacoes"])
TipoIn = Literal["pedagogica", "ocorrencia", "elogio", "reservada"]
DIAS_ATE_ELIMINAR = 30


class AnotacaoIn(BaseModel):
    tipo: TipoIn
    corpo: str = Field(min_length=1, max_length=5000)
    visivel_responsaveis: bool = False


class AnotacaoEdit(BaseModel):
    tipo: TipoIn | None = None
    corpo: str | None = Field(default=None, min_length=1, max_length=5000)
    visivel_responsaveis: bool | None = None


# --- Regras de visibilidade -----------------------------------------------------------------------------------


def _visivel_para_responsaveis(tipo: TipoAnotacao, marcada: bool) -> bool:
    """Elogio sempre; ocorrência só se marcada; pedagógica e reservada nunca."""
    return tipo == TipoAnotacao.elogio or (tipo == TipoAnotacao.ocorrencia and marcada)


def _pode_ver(ctx: Contexto, a: Anotacao) -> bool:
    if a.removida_em is not None and ctx.papel not in STAFF:
        return False
    if ctx.papel in STAFF:
        return True
    if ctx.papel == Papel.professor:
        if a.tipo == TipoAnotacao.reservada:
            return False
        return a.tipo != TipoAnotacao.ocorrencia or a.autor_id == ctx.usuario.id
    if ctx.papel == Papel.responsavel:
        return _visivel_para_responsaveis(a.tipo, a.visivel_responsaveis)
    return False


def _pode_criar(ctx: Contexto, tipo: str) -> None:
    if ctx.papel in LEITORES:
        raise HTTPException(403, "Sem permissão para esta ação.")
    if tipo == TipoAnotacao.reservada and ctx.papel not in STAFF:
        raise HTTPException(403, "Só a direção e a coordenação criam anotações reservadas.")


LEITORES = {Papel.responsavel, Papel.aluno}


def _a_editar(ctx: Contexto, anotacao_id: uuid.UUID) -> Anotacao:
    a = ctx.db.get(Anotacao, anotacao_id)
    if not a or a.removida_em is not None:
        raise HTTPException(404, "Anotação não encontrada.")
    if ctx.papel not in STAFF:
        aluno_visivel(ctx, a.aluno_id)  # quem não é mais professor do aluno não edita
        if ctx.papel != Papel.professor or a.autor_id != ctx.usuario.id:
            raise HTTPException(404, "Anotação não encontrada.")
    return a


def _out(ctx: Contexto, a: Anotacao) -> dict:
    editavel = a.removida_em is None and (
        ctx.papel in STAFF or (ctx.papel == Papel.professor and a.autor_id == ctx.usuario.id)
    )
    out = {
        "id": a.id,
        "tipo": a.tipo,
        "corpo": a.corpo,
        "autor": a.autor.nome if a.autor else None,
        "ano": a.ano_letivo.ano,
        "criado_em": a.criado_em,
        "atualizado_em": a.atualizado_em,
        "visivel_responsaveis": _visivel_para_responsaveis(a.tipo, a.visivel_responsaveis),
        "editavel": editavel,
    }
    if ctx.papel not in LEITORES:
        out |= {"versao": a.versao, "removida": a.removida_em is not None}
    return out


def _nova_versao(ctx: Contexto, a: Anotacao) -> None:
    ctx.db.add(
        AnotacaoVersao(
            escola_id=a.escola_id,
            anotacao_id=a.id,
            versao=a.versao,
            tipo=a.tipo,
            visivel_responsaveis=a.visivel_responsaveis,
            corpo=a.corpo,
            editado_por=ctx.usuario.id,
        )
    )


def _avisa(ctx: Contexto, a: Anotacao, nome_aluno: str, criada: bool) -> None:
    """Família: só quando a anotação é visível a ela e sem o conteúdo no texto. Equipe: ocorrência de professor."""
    if _visivel_para_responsaveis(a.tipo, a.visivel_responsaveis):
        titulo = "Novo elogio" if a.tipo == TipoAnotacao.elogio else "Nova ocorrência registrada"
        notificar(
            ctx.db,
            escola_id=ctx.escola_id,
            usuarios=familia_dos_alunos(ctx.db, ctx.escola_id, [a.aluno_id]),
            tipo="anotacao",
            titulo=titulo,
            corpo=f"Sobre {nome_aluno}. Abra a ficha para ler.",
            url=f"/alunos/{a.aluno_id}",
            excluir=ctx.usuario.id,
        )
    if criada and a.tipo == TipoAnotacao.ocorrencia and ctx.papel == Papel.professor:
        notificar(
            ctx.db,
            escola_id=ctx.escola_id,
            usuarios=equipe_da_escola(ctx.db, ctx.escola_id),
            tipo="anotacao",
            titulo="Nova ocorrência registrada por professor",
            corpo=f"Sobre {nome_aluno}",
            url=f"/alunos/{a.aluno_id}",
            excluir=ctx.usuario.id,
        )


# --- Rotas ----------------------------------------------------------------------------------------------------


@router.get("/alunos/{aluno_id}/anotacoes")
def listar(aluno_id: uuid.UUID, tipo: TipoIn | None = None, ctx: Contexto = Depends(com_perfil)):
    aluno = aluno_visivel(ctx, aluno_id)
    if ctx.papel == Papel.aluno:
        return []
    q = select(Anotacao).where(Anotacao.aluno_id == aluno.id).order_by(Anotacao.criado_em.desc())
    if tipo:
        q = q.where(Anotacao.tipo == tipo)
    itens = [a for a in ctx.db.scalars(q) if _pode_ver(ctx, a)]
    reservadas = [a for a in itens if a.tipo == TipoAnotacao.reservada]
    if reservadas:
        registrar(
            ctx.db,
            "anotacao.reservada_lida",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="aluno",
            entidade_id=aluno.id,
            detalhes={"quantidade": len(reservadas)},
        )
    return [_out(ctx, a) for a in itens]


@router.post("/alunos/{aluno_id}/anotacoes", status_code=201)
def criar(aluno_id: uuid.UUID, body: AnotacaoIn, ctx: Contexto = Depends(com_perfil)):
    aluno = aluno_visivel(ctx, aluno_id)
    _pode_criar(ctx, body.tipo)
    ano = ano_atual(ctx)
    if not ano:
        raise HTTPException(409, "Nenhum ano letivo aberto.")
    a = Anotacao(
        escola_id=ctx.escola_id,
        aluno_id=aluno.id,
        ano_letivo_id=ano.id,
        autor_id=ctx.usuario.id,
        tipo=TipoAnotacao(body.tipo),
        visivel_responsaveis=body.visivel_responsaveis and body.tipo == "ocorrencia",
        corpo=body.corpo.strip(),
    )
    ctx.db.add(a)
    ctx.db.flush()
    _nova_versao(ctx, a)
    registrar(
        ctx.db,
        "anotacao.criar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="anotacao",
        entidade_id=a.id,
        detalhes={"tipo": body.tipo},
    )
    ctx.db.flush()
    ctx.db.refresh(a)
    _avisa(ctx, a, f"{aluno.nome} {aluno.sobrenome}", criada=True)
    return _out(ctx, a)


@router.patch("/anotacoes/{anotacao_id}")
def editar(anotacao_id: uuid.UUID, body: AnotacaoEdit, ctx: Contexto = Depends(com_perfil)):
    a = _a_editar(ctx, anotacao_id)
    dados = body.model_dump(exclude_unset=True)
    novo_tipo = dados.get("tipo", a.tipo.value)
    _pode_criar(ctx, novo_tipo)
    if a.tipo == TipoAnotacao.reservada and ctx.papel not in STAFF:
        raise HTTPException(404, "Anotação não encontrada.")
    era_visivel = _visivel_para_responsaveis(a.tipo, a.visivel_responsaveis)
    a.tipo = TipoAnotacao(novo_tipo)
    if "corpo" in dados and dados["corpo"]:
        a.corpo = dados["corpo"].strip()
    marcada = dados.get("visivel_responsaveis", a.visivel_responsaveis)
    a.visivel_responsaveis = bool(marcada) and a.tipo == TipoAnotacao.ocorrencia
    a.versao += 1
    a.atualizado_em = datetime.now(UTC)
    ctx.db.flush()
    _nova_versao(ctx, a)
    registrar(
        ctx.db,
        "anotacao.editar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="anotacao",
        entidade_id=a.id,
        detalhes={"versao": a.versao},
    )
    if not era_visivel:  # só avisa a família quando a anotação passa a ficar visível para ela
        aluno = ctx.db.get(Aluno, a.aluno_id)
        nome = f"{aluno.nome} {aluno.sobrenome}" if aluno else "o aluno"
        _avisa(ctx, a, nome, criada=False)
    return _out(ctx, a)


@router.delete("/anotacoes/{anotacao_id}", status_code=204)
def remover(anotacao_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    a = _a_editar(ctx, anotacao_id)
    a.removida_em, a.removida_por = datetime.now(UTC), ctx.usuario.id
    registrar(
        ctx.db,
        "anotacao.remover",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="anotacao",
        entidade_id=a.id,
    )


@router.get("/anotacoes/{anotacao_id}/versoes")
def versoes(anotacao_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    """Histórico de edições: só o autor e a equipe (a família vê apenas a versão atual)."""
    a = ctx.db.get(Anotacao, anotacao_id)
    if not a or ctx.papel in LEITORES:
        raise HTTPException(404, "Anotação não encontrada.")
    if ctx.papel not in STAFF:
        aluno_visivel(ctx, a.aluno_id)
        if a.autor_id != ctx.usuario.id or a.removida_em is not None:
            raise HTTPException(404, "Anotação não encontrada.")
    return [
        {
            "versao": v.versao,
            "tipo": v.tipo,
            "corpo": v.corpo,
            "visivel_responsaveis": v.visivel_responsaveis,
            "editado_por": v.editor.nome if v.editor else None,
            "criado_em": v.criado_em,
        }
        for v in ctx.db.scalars(
            select(AnotacaoVersao).where(AnotacaoVersao.anotacao_id == a.id).order_by(AnotacaoVersao.versao.desc())
        )
    ]
