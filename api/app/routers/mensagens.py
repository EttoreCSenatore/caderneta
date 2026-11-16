"""Mensagens individuais: conversas sobre um aluno entre a escola e os responsáveis dele.

Quem vê uma conversa: o profissional da escola envolvido, a direção/coordenação (transparência, com acesso
auditado) e os responsáveis do aluno sem vínculo restrito. A conta do aluno não participa.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.audit import registrar
from app.deps import Contexto, aluno_visivel, com_perfil, ids_alunos_visiveis
from app.models import STAFF, Aluno, Atribuicao, Conversa, ConversaLeitura, Matricula, Mensagem, Papel
from app.notificacoes import familia_dos_alunos, notificar
from app.routers.escola import ano_atual

router = APIRouter(tags=["mensagens"])


class ConversaIn(BaseModel):
    aluno_id: uuid.UUID
    assunto: str = Field(min_length=1, max_length=200)
    corpo: str = Field(min_length=1, max_length=5000)
    professor_id: uuid.UUID | None = None  # só quando o responsável inicia: com quem falar


class MensagemIn(BaseModel):
    corpo: str = Field(min_length=1, max_length=5000)


def _sem_aluno(ctx: Contexto) -> None:
    if ctx.papel == Papel.aluno:
        raise HTTPException(403, "Sem permissão para esta ação.")


def _conversa(ctx: Contexto, conversa_id: uuid.UUID) -> Conversa:
    c = ctx.db.get(Conversa, conversa_id)
    ok = c is not None and ctx.papel != Papel.aluno
    if ok and ctx.papel not in STAFF and c.escola_usuario_id != ctx.usuario.id:
        ok = ctx.papel == Papel.responsavel and bool(
            ctx.db.scalar(select(Aluno.id).where(Aluno.id == c.aluno_id, Aluno.id.in_(ids_alunos_visiveis(ctx))))
        )
    if not ok:
        raise HTTPException(404, "Conversa não encontrada.")
    return c


def _lido_ate(ctx: Contexto, ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime]:
    q = select(ConversaLeitura.conversa_id, ConversaLeitura.lido_ate).where(
        ConversaLeitura.usuario_id == ctx.usuario.id, ConversaLeitura.conversa_id.in_(ids)
    )
    return {i: t for i, t in ctx.db.execute(q)}


def _nao_lida(c: Conversa, lido: datetime | None, uid: uuid.UUID) -> bool:
    return c.ultima_autor_id != uid and (lido is None or c.ultima_em > lido)


def _resumo(c: Conversa, nao_lida: bool) -> dict:
    return {
        "id": c.id,
        "assunto": c.assunto,
        "aluno_id": c.aluno_id,
        "aluno": f"{c.aluno.nome} {c.aluno.sobrenome}",
        "escola_usuario": c.escola_usuario.nome,
        "ultima_em": c.ultima_em,
        "previa": c.ultima_previa,
        "nao_lida": nao_lida,
    }


def _adiciona(ctx: Contexto, c: Conversa, corpo: str) -> Mensagem:
    agora = datetime.now(UTC)
    m = Mensagem(
        escola_id=ctx.escola_id, conversa_id=c.id, autor_id=ctx.usuario.id, corpo=corpo.strip(), criado_em=agora
    )
    ctx.db.add(m)
    c.ultima_em, c.ultima_autor_id, c.ultima_previa = agora, ctx.usuario.id, m.corpo[:140]
    _marca_lida(ctx, c, agora)
    # avisa o outro lado: a família quando escreve a escola, o profissional quando escreve a família
    if ctx.papel == Papel.responsavel:
        destino = {c.escola_usuario_id}
    else:
        destino = set(familia_dos_alunos(ctx.db, ctx.escola_id, [c.aluno_id]))
    notificar(
        ctx.db,
        escola_id=ctx.escola_id,
        usuarios=destino,
        tipo="mensagem",
        titulo="Nova mensagem",
        corpo=f"De {ctx.usuario.nome}",
        url="/mensagens",
        excluir=ctx.usuario.id,
        agora=agora,
    )
    return m


def _marca_lida(ctx: Contexto, c: Conversa, ate: datetime) -> None:
    ctx.db.execute(
        insert(ConversaLeitura)
        .values(id=uuid.uuid4(), escola_id=ctx.escola_id, conversa_id=c.id, usuario_id=ctx.usuario.id, lido_ate=ate)
        .on_conflict_do_update(index_elements=["conversa_id", "usuario_id"], set_={"lido_ate": ate})
    )


@router.post("/conversas", status_code=201)
def criar(body: ConversaIn, ctx: Contexto = Depends(com_perfil)):
    _sem_aluno(ctx)
    aluno = aluno_visivel(ctx, body.aluno_id)
    if ctx.papel == Papel.responsavel:
        # o responsável escolhe um professor da turma do filho
        ano = ano_atual(ctx)
        turma = None
        if ano:
            turma = ctx.db.scalar(
                select(Matricula.turma_id).where(Matricula.aluno_id == aluno.id, Matricula.ano_letivo_id == ano.id)
            )
        profs = set(ctx.db.scalars(select(Atribuicao.professor_id).where(Atribuicao.turma_id == turma)))
        if body.professor_id not in profs:
            raise HTTPException(422, "Escolha um professor da turma do aluno.")
        escola_usuario = body.professor_id
    else:
        escola_usuario = ctx.usuario.id
    c = Conversa(
        escola_id=ctx.escola_id, aluno_id=aluno.id, escola_usuario_id=escola_usuario, assunto=body.assunto.strip()
    )
    ctx.db.add(c)
    ctx.db.flush()
    _adiciona(ctx, c, body.corpo)
    ctx.db.flush()
    ctx.db.refresh(c)
    registrar(
        ctx.db,
        "conversa.criar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="conversa",
        entidade_id=c.id,
    )
    return _resumo(c, False)


@router.get("/conversas")
def listar(ctx: Contexto = Depends(com_perfil)):
    if ctx.papel == Papel.aluno:
        return []
    q = select(Conversa).order_by(Conversa.ultima_em.desc()).limit(200)
    if ctx.papel == Papel.professor:
        q = q.where(Conversa.escola_usuario_id == ctx.usuario.id)
    elif ctx.papel == Papel.responsavel:
        q = q.where(Conversa.aluno_id.in_(ids_alunos_visiveis(ctx)))
    cs = list(ctx.db.scalars(q))
    lido = _lido_ate(ctx, [c.id for c in cs])
    return [_resumo(c, _nao_lida(c, lido.get(c.id), ctx.usuario.id)) for c in cs]


@router.get("/conversas/{conversa_id}")
def abrir(conversa_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    """Mensagens da conversa; marca como lida. A equipe que não faz parte dela fica registrada na auditoria."""
    c = _conversa(ctx, conversa_id)
    if ctx.papel in STAFF and c.escola_usuario_id != ctx.usuario.id:
        registrar(
            ctx.db,
            "conversa.supervisao",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="conversa",
            entidade_id=c.id,
        )
    ms = list(ctx.db.scalars(select(Mensagem).where(Mensagem.conversa_id == c.id).order_by(Mensagem.criado_em)))
    _marca_lida(ctx, c, c.ultima_em)
    return {
        **_resumo(c, False),
        "mensagens": [
            {
                "id": m.id,
                "autor": m.autor.nome if m.autor else None,
                "minha": m.autor_id == ctx.usuario.id,
                "corpo": m.corpo,
                "criado_em": m.criado_em,
            }
            for m in ms
        ],
    }


@router.post("/conversas/{conversa_id}/mensagens", status_code=201)
def responder(conversa_id: uuid.UUID, body: MensagemIn, ctx: Contexto = Depends(com_perfil)):
    c = _conversa(ctx, conversa_id)
    m = _adiciona(ctx, c, body.corpo)
    ctx.db.flush()
    return {"id": m.id, "autor": ctx.usuario.nome, "minha": True, "corpo": m.corpo, "criado_em": m.criado_em}


@router.get("/mensagens-pendentes")
def pendentes(ctx: Contexto = Depends(com_perfil)):
    """Número de conversas com mensagem nova (selo do menu)."""
    if ctx.papel == Papel.aluno:
        return {"nao_lidas": 0}
    q = (
        select(func.count())
        .select_from(Conversa)
        .outerjoin(
            ConversaLeitura,
            (ConversaLeitura.conversa_id == Conversa.id) & (ConversaLeitura.usuario_id == ctx.usuario.id),
        )
    )
    q = q.where(
        func.coalesce(Conversa.ultima_autor_id != ctx.usuario.id, True),
        (ConversaLeitura.lido_ate.is_(None)) | (Conversa.ultima_em > ConversaLeitura.lido_ate),
    )
    if ctx.papel == Papel.professor or ctx.papel in STAFF:
        q = q.where(Conversa.escola_usuario_id == ctx.usuario.id)  # equipe só conta as próprias
    else:
        q = q.where(Conversa.aluno_id.in_(ids_alunos_visiveis(ctx)))
    return {"nao_lidas": ctx.db.scalar(q)}
