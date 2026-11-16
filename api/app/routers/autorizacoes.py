"""Autorizações digitais (passeio, saída antecipada): o responsável autoriza ou não, aluno por aluno."""

import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select

from app.audit import registrar
from app.deps import Contexto, aluno_visivel, com_perfil
from app.models import (
    STAFF,
    Aluno,
    Autorizacao,
    AutorizacaoResposta,
    Matricula,
    Papel,
    Turma,
    VinculoResponsavel,
)
from app.notificacoes import familia_dos_alunos, notificar
from app.routers.avisos import LEITORES, _pode_escrever
from app.routers.escola import ano_atual
from app.routers.turmas import turmas_visiveis

router = APIRouter(tags=["autorizacoes"])


class AutorizacaoIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=1, max_length=5000)
    turma_id: uuid.UUID | None = None
    data_evento: date | None = None
    prazo: datetime | None = None


class RespostaIn(BaseModel):
    autoriza: bool
    observacao: str | None = Field(default=None, max_length=300)


def _editavel(ctx: Contexto, autorizacao_id: uuid.UUID) -> Autorizacao:
    a = ctx.db.get(Autorizacao, autorizacao_id)
    if not a or (ctx.papel not in STAFF and a.autor_id != ctx.usuario.id):
        raise HTTPException(404, "Autorização não encontrada.")
    return a


def _alunos_alvo(ctx: Contexto, a: Autorizacao) -> list[Aluno]:
    """Alunos matriculados no ano atual a quem o pedido se dirige."""
    ano = ano_atual(ctx)
    if not ano:
        return []
    q = (
        select(Aluno)
        .join(Matricula, Matricula.aluno_id == Aluno.id)
        .where(Matricula.ano_letivo_id == ano.id)
        .order_by(Aluno.nome, Aluno.sobrenome)
    )
    if a.turma_id:
        q = q.where(Matricula.turma_id == a.turma_id)
    return list(ctx.db.scalars(q))


def _out(a: Autorizacao, turma: str | None = None) -> dict:
    return {
        "id": a.id,
        "titulo": a.titulo,
        "descricao": a.descricao,
        "turma_id": a.turma_id,
        "turma": turma,
        "autor": a.autor.nome if a.autor else None,
        "data_evento": a.data_evento,
        "prazo": a.prazo,
        "encerrada": bool(a.prazo and a.prazo < datetime.now(UTC)),
        "arquivado": a.arquivado,
        "criado_em": a.criado_em,
    }


@router.post("/autorizacoes", status_code=201)
def criar(body: AutorizacaoIn, ctx: Contexto = Depends(com_perfil)):
    _pode_escrever(ctx, body.turma_id)
    a = Autorizacao(
        escola_id=ctx.escola_id,
        autor_id=ctx.usuario.id,
        turma_id=body.turma_id,
        titulo=body.titulo.strip(),
        descricao=body.descricao.strip(),
        data_evento=body.data_evento,
        prazo=body.prazo,
    )
    ctx.db.add(a)
    ctx.db.flush()
    familia = familia_dos_alunos(ctx.db, ctx.escola_id, [x.id for x in _alunos_alvo(ctx, a)])
    notificar(
        ctx.db,
        escola_id=ctx.escola_id,
        usuarios=familia,
        tipo="autorizacao",
        titulo="Nova autorização para responder",
        corpo=a.titulo,
        url="/autorizacoes",
        excluir=ctx.usuario.id,
    )
    registrar(
        ctx.db,
        "autorizacao.criar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="autorizacao",
        entidade_id=a.id,
    )
    return _out(a)


@router.get("/autorizacoes")
def listar(ctx: Contexto = Depends(com_perfil), arquivadas: bool = False):
    """Responsável: um item por filho × pedido, com a resposta dada. Equipe/professor: pedidos com contagens."""
    if ctx.papel == Papel.aluno:
        return []
    q = select(Autorizacao).order_by(Autorizacao.criado_em.desc())
    if ctx.papel == Papel.professor:
        q = q.where(or_(Autorizacao.autor_id == ctx.usuario.id, Autorizacao.turma_id.in_(turmas_visiveis(ctx))))
    elif ctx.papel == Papel.responsavel:
        q = q.where(or_(Autorizacao.turma_id.is_(None), Autorizacao.turma_id.in_(turmas_visiveis(ctx))))
    if not arquivadas:
        q = q.where(Autorizacao.arquivado.is_(False))
    pedidos = list(ctx.db.scalars(q.limit(200)))
    nomes = {i: n for i, n in ctx.db.execute(select(Turma.id, Turma.nome))}
    if ctx.papel not in LEITORES:
        resp = list(
            ctx.db.scalars(
                select(AutorizacaoResposta).where(AutorizacaoResposta.autorizacao_id.in_([p.id for p in pedidos]))
            )
        )
        saida = []
        for p in pedidos:
            rs = [r for r in resp if r.autorizacao_id == p.id]
            total = len(_alunos_alvo(ctx, p))
            saida.append(
                {
                    **_out(p, nomes.get(p.turma_id)),
                    "total": total,
                    "autorizados": sum(r.autoriza for r in rs),
                    "negados": sum(not r.autoriza for r in rs),
                    "pendentes": total - len(rs),
                }
            )
        return saida
    # responsável: filhos com vínculo não restrito, matriculados no ano atual
    ano = ano_atual(ctx)
    if not ano:
        return []
    filhos = ctx.db.execute(
        select(Aluno, Matricula.turma_id)
        .join(Matricula, Matricula.aluno_id == Aluno.id)
        .join(VinculoResponsavel, VinculoResponsavel.aluno_id == Aluno.id)
        .where(
            VinculoResponsavel.usuario_id == ctx.usuario.id,
            VinculoResponsavel.restrito.is_(False),
            Matricula.ano_letivo_id == ano.id,
        )
    ).all()
    respostas = {
        (r.autorizacao_id, r.aluno_id): r
        for r in ctx.db.scalars(
            select(AutorizacaoResposta).where(AutorizacaoResposta.autorizacao_id.in_([p.id for p in pedidos]))
        )
    }
    itens = []
    for p in pedidos:
        for aluno, turma_id in filhos:
            if p.turma_id and p.turma_id != turma_id:
                continue
            r = respostas.get((p.id, aluno.id))
            itens.append(
                {
                    **_out(p, nomes.get(p.turma_id)),
                    "aluno_id": aluno.id,
                    "aluno": f"{aluno.nome} {aluno.sobrenome}",
                    "resposta": None if not r else ("autorizo" if r.autoriza else "nao_autorizo"),
                    "observacao": r.observacao if r else None,
                    "respondido_em": r.respondido_em if r else None,
                }
            )
    return itens


@router.put("/autorizacoes/{autorizacao_id}/alunos/{aluno_id}")
def responder(autorizacao_id: uuid.UUID, aluno_id: uuid.UUID, body: RespostaIn, ctx: Contexto = Depends(com_perfil)):
    """O responsável autoriza ou nega por um filho; pode mudar de ideia até o prazo."""
    if ctx.papel != Papel.responsavel:
        raise HTTPException(403, "Só os responsáveis respondem a autorizações.")
    aluno = aluno_visivel(ctx, aluno_id)
    a = ctx.db.get(Autorizacao, autorizacao_id)
    ano = ano_atual(ctx)
    mat = (
        ctx.db.scalar(select(Matricula).where(Matricula.aluno_id == aluno.id, Matricula.ano_letivo_id == ano.id))
        if ano
        else None
    )
    if not a or not mat or (a.turma_id and a.turma_id != mat.turma_id):
        raise HTTPException(404, "Autorização não encontrada.")
    if a.arquivado or (a.prazo and a.prazo < datetime.now(UTC)):
        raise HTTPException(409, "O prazo desta autorização já passou.")
    r = ctx.db.scalar(
        select(AutorizacaoResposta).where(
            AutorizacaoResposta.autorizacao_id == a.id, AutorizacaoResposta.aluno_id == aluno.id
        )
    )
    if not r:
        r = AutorizacaoResposta(escola_id=ctx.escola_id, autorizacao_id=a.id, aluno_id=aluno.id, autoriza=body.autoriza)
        ctx.db.add(r)
    r.autoriza, r.usuario_id = body.autoriza, ctx.usuario.id
    r.observacao = (body.observacao or "").strip() or None
    r.respondido_em = datetime.now(UTC)
    registrar(
        ctx.db,
        "autorizacao.responder",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="autorizacao",
        entidade_id=a.id,
        detalhes={"aluno_id": str(aluno.id), "autoriza": body.autoriza},
    )
    return {"resposta": "autorizo" if r.autoriza else "nao_autorizo", "respondido_em": r.respondido_em}


@router.get("/autorizacoes/{autorizacao_id}/painel")
def painel(autorizacao_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    """Situação de cada aluno do público. Só para quem criou ou a equipe."""
    a = _editavel(ctx, autorizacao_id)
    respostas = {
        r.aluno_id: r
        for r in ctx.db.scalars(select(AutorizacaoResposta).where(AutorizacaoResposta.autorizacao_id == a.id))
    }
    linhas = []
    for al in _alunos_alvo(ctx, a):
        r = respostas.get(al.id)
        linhas.append(
            {
                "aluno_id": al.id,
                "aluno": f"{al.nome} {al.sobrenome}",
                "situacao": "pendente" if not r else ("autorizado" if r.autoriza else "negado"),
                "observacao": r.observacao if r else None,
                "respondido_em": r.respondido_em if r else None,
            }
        )
    cont = {k: sum(1 for x in linhas if x["situacao"] == k) for k in ("autorizado", "negado", "pendente")}
    return {"autorizacao": _out(a), "total": len(linhas), **cont, "alunos": linhas}


@router.post("/autorizacoes/{autorizacao_id}/arquivar")
def arquivar(autorizacao_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    a = _editavel(ctx, autorizacao_id)
    a.arquivado = True
    registrar(
        ctx.db,
        "autorizacao.arquivar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="autorizacao",
        entidade_id=a.id,
    )
    return _out(a)
