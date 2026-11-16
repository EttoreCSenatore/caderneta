"""Avisos da escola e de turma, com agendamento, "ciente" e painel de leitura."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert

from app.audit import registrar
from app.deps import Contexto, com_perfil
from app.models import (
    STAFF,
    Aluno,
    Aviso,
    AvisoLeitura,
    EscopoAviso,
    Matricula,
    Papel,
    Turma,
    Usuario,
    VinculoResponsavel,
)
from app.routers.escola import ano_atual
from app.routers.turmas import turma_visivel, turmas_visiveis

router = APIRouter(tags=["avisos"])
LEITORES = {Papel.responsavel, Papel.aluno}


class AvisoIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    corpo: str = Field(min_length=1, max_length=10000)
    turma_id: uuid.UUID | None = None  # vazio = escola inteira (só direção/coordenação)
    exige_ciente: bool = False
    publicar_em: datetime | None = None


def _pode_escrever(ctx: Contexto, turma_id: uuid.UUID | None) -> None:
    if ctx.papel in LEITORES:
        raise HTTPException(403, "Sem permissão para esta ação.")
    if turma_id is None:
        if ctx.papel not in STAFF:
            raise HTTPException(403, "Só a direção e a coordenação enviam avisos para a escola toda.")
    else:
        turma_visivel(ctx, turma_id)  # 404 se o professor não leciona nessa turma


def _aviso_editavel(ctx: Contexto, aviso_id: uuid.UUID) -> Aviso:
    a = ctx.db.get(Aviso, aviso_id)
    if not a or (ctx.papel not in STAFF and a.autor_id != ctx.usuario.id):
        raise HTTPException(404, "Aviso não encontrado.")
    return a


def destinatarios(ctx: Contexto, aviso: Aviso) -> dict[uuid.UUID, str]:
    """Usuários que devem ler o aviso: responsáveis com acesso (não restritos) e alunos com conta."""
    ano = ano_atual(ctx)
    if not ano:
        return {}
    alunos = select(Matricula.aluno_id).where(Matricula.ano_letivo_id == ano.id)
    if aviso.turma_id:
        alunos = alunos.where(Matricula.turma_id == aviso.turma_id)
    res: dict[uuid.UUID, str] = {}
    q1 = (
        select(Usuario.id, Usuario.nome)
        .join(VinculoResponsavel, VinculoResponsavel.usuario_id == Usuario.id)
        .where(VinculoResponsavel.aluno_id.in_(alunos), VinculoResponsavel.restrito.is_(False))
    )
    q2 = select(Usuario.id, Usuario.nome).join(Aluno, Aluno.usuario_id == Usuario.id).where(Aluno.id.in_(alunos))
    for uid, nome in [*ctx.db.execute(q1), *ctx.db.execute(q2)]:
        res[uid] = nome
    return res


def aviso_out(a: Aviso, leitura: AvisoLeitura | None = None, turma_nome: str | None = None) -> dict:
    return {
        "id": a.id,
        "titulo": a.titulo,
        "corpo": a.corpo,
        "escopo": a.escopo,
        "turma_id": a.turma_id,
        "turma": turma_nome,
        "autor": a.autor.nome if a.autor else None,
        "exige_ciente": a.exige_ciente,
        "publicar_em": a.publicar_em,
        "arquivado": a.arquivado,
        "lido": bool(leitura),
        "ciente": bool(leitura and leitura.ciente_em),
    }


@router.post("/avisos", status_code=201)
def criar(body: AvisoIn, ctx: Contexto = Depends(com_perfil)):
    _pode_escrever(ctx, body.turma_id)
    a = Aviso(
        escola_id=ctx.escola_id,
        autor_id=ctx.usuario.id,
        escopo=EscopoAviso.turma if body.turma_id else EscopoAviso.escola,
        turma_id=body.turma_id,
        titulo=body.titulo.strip(),
        corpo=body.corpo.strip(),
        exige_ciente=body.exige_ciente,
        publicar_em=body.publicar_em or datetime.now(UTC),
    )
    ctx.db.add(a)
    ctx.db.flush()
    registrar(
        ctx.db, "aviso.criar", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, entidade="aviso", entidade_id=a.id
    )
    return aviso_out(a)


@router.get("/avisos")
def listar(ctx: Contexto = Depends(com_perfil), arquivados: bool = False):
    """Caixa de entrada. Leitores veem só o já publicado; autores veem também os agendados deles."""
    q = select(Aviso).order_by(Aviso.publicar_em.desc())
    agora = datetime.now(UTC)
    if ctx.papel in STAFF:
        pass
    elif ctx.papel in LEITORES:
        q = q.where(Aviso.publicar_em <= agora)
    else:
        q = q.where(or_(Aviso.publicar_em <= agora, Aviso.autor_id == ctx.usuario.id))
    if (escopo := turmas_visiveis(ctx)) is not None:
        q = q.where(or_(Aviso.turma_id.is_(None), Aviso.turma_id.in_(escopo)))
    if not arquivados:
        q = q.where(Aviso.arquivado.is_(False))
    avisos = list(ctx.db.scalars(q.limit(200)))
    leituras = {
        lt.aviso_id: lt
        for lt in ctx.db.scalars(
            select(AvisoLeitura).where(
                AvisoLeitura.usuario_id == ctx.usuario.id, AvisoLeitura.aviso_id.in_([a.id for a in avisos])
            )
        )
    }
    nomes = {i: n for i, n in ctx.db.execute(select(Turma.id, Turma.nome))}
    return [aviso_out(a, leituras.get(a.id), nomes.get(a.turma_id)) for a in avisos]


def _aviso_visivel(ctx: Contexto, aviso_id: uuid.UUID) -> Aviso:
    a = ctx.db.get(Aviso, aviso_id)
    ok = a is not None
    if ok and ctx.papel not in STAFF:
        if a.turma_id and (escopo := turmas_visiveis(ctx)) is not None:
            ok = a.turma_id in set(ctx.db.scalars(escopo))
        if ok and a.publicar_em > datetime.now(UTC):
            ok = ctx.papel not in LEITORES and a.autor_id == ctx.usuario.id
    if not ok:
        raise HTTPException(404, "Aviso não encontrado.")
    return a


@router.post("/avisos/{aviso_id}/lido")
def marcar_lido(aviso_id: uuid.UUID, ciente: bool = False, ctx: Contexto = Depends(com_perfil)):
    """Registra a leitura (e o "ciente", se pedido). Idempotente; o primeiro horário é preservado."""
    a = _aviso_visivel(ctx, aviso_id)
    if ctx.papel not in LEITORES:
        return aviso_out(a)
    agora = datetime.now(UTC)
    ctx.db.execute(
        insert(AvisoLeitura)
        .values(
            id=uuid.uuid4(),
            escola_id=ctx.escola_id,
            aviso_id=a.id,
            usuario_id=ctx.usuario.id,
            lido_em=agora,
            ciente_em=agora if ciente else None,
        )
        .on_conflict_do_nothing(index_elements=["aviso_id", "usuario_id"])
    )
    lt = ctx.db.scalar(
        select(AvisoLeitura).where(AvisoLeitura.aviso_id == a.id, AvisoLeitura.usuario_id == ctx.usuario.id)
    )
    if ciente and not lt.ciente_em:
        lt.ciente_em = agora
    return aviso_out(a, lt)


@router.get("/avisos/{aviso_id}/painel")
def painel(aviso_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    """Quem já leu / deu ciente e quem falta. Só para quem enviou (ou direção/coordenação)."""
    a = _aviso_editavel(ctx, aviso_id)
    dest = destinatarios(ctx, a)
    leituras = {lt.usuario_id: lt for lt in ctx.db.scalars(select(AvisoLeitura).where(AvisoLeitura.aviso_id == a.id))}
    linhas = [
        {
            "usuario_id": uid,
            "nome": nome,
            "lido_em": leituras[uid].lido_em if uid in leituras else None,
            "ciente_em": leituras[uid].ciente_em if uid in leituras else None,
        }
        for uid, nome in sorted(dest.items(), key=lambda x: x[1])
    ]
    return {
        "aviso": aviso_out(a),
        "total": len(linhas),
        "lidos": sum(1 for r in linhas if r["lido_em"]),
        "cientes": sum(1 for r in linhas if r["ciente_em"]),
        "destinatarios": linhas,
    }


@router.post("/avisos/{aviso_id}/arquivar")
def arquivar(aviso_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    a = _aviso_editavel(ctx, aviso_id)
    a.arquivado = True
    registrar(
        ctx.db, "aviso.arquivar", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, entidade="aviso", entidade_id=a.id
    )
    return aviso_out(a)


@router.get("/avisos-pendentes")
def pendentes(ctx: Contexto = Depends(com_perfil)):
    """Quantidade de avisos publicados que o leitor ainda não leu (selo do menu)."""
    if ctx.papel not in LEITORES:
        return {"nao_lidos": 0}
    q = (
        select(func.count())
        .select_from(Aviso)
        .where(Aviso.publicar_em <= datetime.now(UTC), Aviso.arquivado.is_(False))
    )
    if (escopo := turmas_visiveis(ctx)) is not None:
        q = q.where(or_(Aviso.turma_id.is_(None), Aviso.turma_id.in_(escopo)))
    q = q.where(~Aviso.id.in_(select(AvisoLeitura.aviso_id).where(AvisoLeitura.usuario_id == ctx.usuario.id)))
    return {"nao_lidos": ctx.db.scalar(q)}
