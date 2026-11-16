"""Calendário escolar: eventos da escola e das turmas, feriados, dias sem aula e assinatura iCal."""

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.audit import registrar
from app.calendario import feriados_sugeridos, ics
from app.config import get_settings
from app.db import get_db, set_ctx
from app.deps import Contexto, com_perfil, equipe
from app.models import (
    BLOQUEIA_AULA,
    STAFF,
    Atribuicao,
    Aula,
    Avaliacao,
    CalendarioToken,
    Escola,
    Evento,
    Papel,
    TipoEvento,
    Turma,
    Usuario,
    UsuarioPerfil,
)
from app.notificacoes import alunos_do_publico, familia_dos_alunos, notificar
from app.routers.turmas import turma_visivel, turmas_visiveis
from app.security import hash_token, novo_token

router = APIRouter(tags=["calendario"])
LEITORES = {Papel.responsavel, Papel.aluno}
MAX_DIAS = 400


class EventoIn(BaseModel):
    tipo: TipoEvento
    titulo: str = Field(min_length=1, max_length=200)
    descricao: str | None = Field(default=None, max_length=1000)
    inicio: date
    fim: date | None = None
    turma_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _ordem(self):
        if self.fim and self.fim < self.inicio:
            raise ValueError("A data final não pode ser antes da inicial.")
        return self


class FeriadosIn(BaseModel):
    ano: int = Field(ge=2000, le=2100)
    datas: list[date] = Field(min_length=1, max_length=30)


def _pode_criar(ctx: Contexto, tipo: TipoEvento, turma_id: uuid.UUID | None) -> None:
    if ctx.papel in LEITORES:
        raise HTTPException(403, "Sem permissão para esta ação.")
    if ctx.papel in STAFF:
        if turma_id:
            turma_visivel(ctx, turma_id)
        return
    # professor: só eventos de turma, e nunca feriado nem dia sem aula (que bloqueiam a chamada)
    if turma_id is None or tipo in BLOQUEIA_AULA:
        raise HTTPException(403, "Só a direção e a coordenação cadastram eventos da escola, feriados e dias sem aula.")
    turma_visivel(ctx, turma_id)


def _evento_do_autor(ctx: Contexto, evento_id: uuid.UUID) -> Evento:
    e = ctx.db.get(Evento, evento_id)
    if not e or (ctx.papel not in STAFF and (e.autor_id != ctx.usuario.id or ctx.papel in LEITORES)):
        raise HTTPException(404, "Evento não encontrado.")
    return e


def _evento_out(e: Evento, turma: str | None, editavel: bool) -> dict:
    return {
        "id": e.id,
        "origem": "evento",
        "tipo": e.tipo,
        "titulo": e.titulo,
        "descricao": e.descricao,
        "inicio": e.inicio,
        "fim": e.fim,
        "turma_id": e.turma_id,
        "turma": turma,
        "autor": e.autor.nome if e.autor else None,
        "editavel": editavel,
    }


def itens_do_periodo(ctx: Contexto, inicio: date, fim: date, turma_id: uuid.UUID | None = None) -> list[dict]:
    """Eventos visíveis ao perfil + avaliações com data nas turmas visíveis."""
    escopo = turmas_visiveis(ctx)
    nomes = {i: n for i, n in ctx.db.execute(select(Turma.id, Turma.nome))}
    q = select(Evento).where(Evento.inicio <= fim, Evento.fim >= inicio).order_by(Evento.inicio, Evento.titulo)
    if escopo is not None:
        q = q.where(or_(Evento.turma_id.is_(None), Evento.turma_id.in_(escopo)))
    if turma_id:
        q = q.where(or_(Evento.turma_id.is_(None), Evento.turma_id == turma_id))
    itens = []
    for e in ctx.db.scalars(q):
        editavel = ctx.papel in STAFF or (ctx.papel == Papel.professor and e.autor_id == ctx.usuario.id)
        itens.append(_evento_out(e, nomes.get(e.turma_id), editavel))
    qa = (
        select(Avaliacao, Atribuicao, Turma)
        .join(Atribuicao, Atribuicao.id == Avaliacao.atribuicao_id)
        .join(Turma, Turma.id == Atribuicao.turma_id)
        .where(Avaliacao.data.is_not(None), Avaliacao.data >= inicio, Avaliacao.data <= fim)
    )
    if escopo is not None:
        qa = qa.where(Turma.id.in_(escopo))
    if turma_id:
        qa = qa.where(Turma.id == turma_id)
    for av, at, t in ctx.db.execute(qa):
        itens.append(
            {
                "id": av.id,
                "origem": "avaliacao",
                "tipo": "avaliacao",
                "titulo": f"{av.nome} · {at.disciplina.nome}",
                "descricao": None,
                "inicio": av.data,
                "fim": av.data,
                "turma_id": t.id,
                "turma": t.nome,
                "autor": at.professor.nome,
                "editavel": False,
            }
        )
    return sorted(itens, key=lambda i: (i["inicio"], i["titulo"]))


@router.get("/calendario")
def calendario(inicio: date, fim: date, turma_id: uuid.UUID | None = None, ctx: Contexto = Depends(com_perfil)):
    if fim < inicio or (fim - inicio).days > MAX_DIAS:
        raise HTTPException(422, f"Período inválido (máximo de {MAX_DIAS} dias).")
    if turma_id:
        turma_visivel(ctx, turma_id)
    return itens_do_periodo(ctx, inicio, fim, turma_id)


@router.post("/calendario/eventos", status_code=201)
def criar(body: EventoIn, ctx: Contexto = Depends(com_perfil)):
    _pode_criar(ctx, body.tipo, body.turma_id)
    e = Evento(
        escola_id=ctx.escola_id,
        autor_id=ctx.usuario.id,
        turma_id=body.turma_id,
        tipo=body.tipo,
        titulo=body.titulo.strip(),
        descricao=(body.descricao or "").strip() or None,
        inicio=body.inicio,
        fim=body.fim or body.inicio,
    )
    ctx.db.add(e)
    ctx.db.flush()
    out = _evento_out(e, None, True)
    if e.tipo == TipoEvento.sem_aula:
        out["aulas_ja_registradas"] = _aulas_no_periodo(ctx, e)
        quando = e.inicio.strftime("%d/%m") + (f" a {e.fim:%d/%m}" if e.fim != e.inicio else "")
        notificar(
            ctx.db,
            escola_id=ctx.escola_id,
            usuarios=familia_dos_alunos(
                ctx.db, ctx.escola_id, alunos_do_publico(ctx.db, ctx.escola_id, e.turma_id), incluir_alunos=True
            ),
            tipo="calendario",
            titulo="Dia sem aula",
            corpo=f"{e.titulo} ({quando})",
            url="/calendario",
            excluir=ctx.usuario.id,
        )
    registrar(
        ctx.db,
        "evento.criar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="evento",
        entidade_id=e.id,
        detalhes={"tipo": e.tipo.value},
    )
    return out


def _aulas_no_periodo(ctx: Contexto, e: Evento) -> int:
    """Aulas já registradas nas datas do evento (aviso para a equipe revisar; nada é apagado)."""
    q = (
        select(func.count())
        .select_from(Aula)
        .join(Atribuicao, Atribuicao.id == Aula.atribuicao_id)
        .where(Aula.data >= e.inicio, Aula.data <= e.fim)
    )
    if e.turma_id:
        q = q.where(Atribuicao.turma_id == e.turma_id)
    return ctx.db.scalar(q) or 0


@router.patch("/calendario/eventos/{evento_id}")
def editar(evento_id: uuid.UUID, body: EventoIn, ctx: Contexto = Depends(com_perfil)):
    e = _evento_do_autor(ctx, evento_id)
    _pode_criar(ctx, body.tipo, body.turma_id)
    e.tipo, e.turma_id, e.titulo = body.tipo, body.turma_id, body.titulo.strip()
    e.descricao = (body.descricao or "").strip() or None
    e.inicio, e.fim = body.inicio, body.fim or body.inicio
    return _evento_out(e, None, True)


@router.delete("/calendario/eventos/{evento_id}", status_code=204)
def remover(evento_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    e = _evento_do_autor(ctx, evento_id)
    registrar(
        ctx.db,
        "evento.remover",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="evento",
        entidade_id=e.id,
    )
    ctx.db.delete(e)


# --- Feriados nacionais -----------------------------------------------------------------------------------


@router.get("/calendario/feriados-sugeridos")
def sugeridos(ano: int, ctx: Contexto = Depends(equipe)):
    """Datas para a escola confirmar. As que já estão no calendário vêm marcadas."""
    if not 2000 <= ano <= 2100:
        raise HTTPException(422, "Ano inválido.")
    ja = set(
        ctx.db.scalars(
            select(Evento.inicio).where(
                Evento.tipo.in_(list(BLOQUEIA_AULA)),
                Evento.turma_id.is_(None),
                Evento.inicio >= date(ano, 1, 1),
                Evento.inicio <= date(ano, 12, 31),
            )
        )
    )
    return [{**f, "ja_cadastrado": f["data"] in ja} for f in feriados_sugeridos(ano)]


@router.post("/calendario/feriados", status_code=201)
def importar(body: FeriadosIn, ctx: Contexto = Depends(equipe)):
    """Cria os feriados escolhidos (só datas da lista sugerida). Repetir a chamada não duplica."""
    validos = {f["data"]: f for f in feriados_sugeridos(body.ano)}
    if any(d not in validos for d in body.datas):
        raise HTTPException(422, "Há datas fora da lista de feriados sugeridos.")
    ja = set(
        ctx.db.scalars(select(Evento.inicio).where(Evento.turma_id.is_(None), Evento.tipo.in_(list(BLOQUEIA_AULA))))
    )
    criados = 0
    for d in sorted(set(body.datas)):
        if d in ja:
            continue
        f = validos[d]
        ctx.db.add(
            Evento(
                escola_id=ctx.escola_id,
                autor_id=ctx.usuario.id,
                tipo=TipoEvento.feriado if f["nacional"] else TipoEvento.sem_aula,
                titulo=f["nome"],
                descricao=f["base"],
                inicio=d,
                fim=d,
            )
        )
        criados += 1
    registrar(
        ctx.db,
        "calendario.feriados",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        detalhes={"ano": body.ano, "criados": criados},
    )
    return {"criados": criados}


# --- Assinatura iCal --------------------------------------------------------------------------------------


def _perfil_ativo(ctx: Contexto) -> UsuarioPerfil:
    assert ctx.perfil is not None
    return ctx.perfil


@router.get("/calendario-ical")
def ical_status(ctx: Contexto = Depends(com_perfil)):
    t = ctx.db.scalar(select(CalendarioToken).where(CalendarioToken.perfil_id == _perfil_ativo(ctx).id))
    return {"ativo": t is not None, "criado_em": t.criado_em if t else None}


@router.post("/calendario-ical", status_code=201)
def ical_criar(ctx: Contexto = Depends(com_perfil)):
    """Gera (ou troca) o link de assinatura. O link aparece só agora; quem tem o link vê o calendário."""
    perfil = _perfil_ativo(ctx)
    antigo = ctx.db.scalar(select(CalendarioToken).where(CalendarioToken.perfil_id == perfil.id))
    if antigo:
        ctx.db.delete(antigo)
        ctx.db.flush()
    token, h = novo_token()
    ctx.db.add(CalendarioToken(escola_id=ctx.escola_id, perfil_id=perfil.id, token_hash=h))
    registrar(
        ctx.db, "calendario.ical_gerar", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, entidade="calendario_token"
    )
    base = get_settings().public_url.rstrip("/")
    return {"url": f"{base}/api/calendario/ical/{ctx.escola_id}.{token}.ics"}


@router.delete("/calendario-ical", status_code=204)
def ical_revogar(ctx: Contexto = Depends(com_perfil)):
    t = ctx.db.scalar(select(CalendarioToken).where(CalendarioToken.perfil_id == _perfil_ativo(ctx).id))
    if t:
        ctx.db.delete(t)
        registrar(
            ctx.db,
            "calendario.ical_revogar",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="calendario_token",
        )


def _contexto_do_token(db: Session, token: str) -> Contexto:
    """Autentica pelo link: `<escola>.<segredo>`. Qualquer falha vira o mesmo 404."""
    try:
        escola_txt, segredo = token.split(".", 1)
        escola_id = uuid.UUID(escola_txt)
    except ValueError:
        raise HTTPException(404, "Calendário não encontrado.") from None
    set_ctx(db, escola_id=escola_id)
    t = db.scalar(select(CalendarioToken).where(CalendarioToken.token_hash == hash_token(segredo)))
    perfil = db.get(UsuarioPerfil, t.perfil_id) if t else None
    if not t or not perfil or not perfil.ativo or perfil.escola_id != escola_id:
        raise HTTPException(404, "Calendário não encontrado.")
    set_ctx(db, usuario_id=perfil.usuario_id)
    usuario = db.get(Usuario, perfil.usuario_id)
    if not usuario or not usuario.ativo:
        raise HTTPException(404, "Calendário não encontrado.")
    return Contexto(db, None, usuario, perfil)  # type: ignore[arg-type]


@router.get("/calendario/ical/{token}.ics")
def ical(token: str, db: Session = Depends(get_db, scope="function")):
    ctx = _contexto_do_token(db, token)
    hoje = datetime.now(UTC).date()
    itens = itens_do_periodo(ctx, hoje - timedelta(days=60), hoje + timedelta(days=MAX_DIAS))
    escola = db.get(Escola, ctx.escola_id)
    exibidos = [{**i, "titulo": f"[{i['turma']}] {i['titulo']}" if i["turma"] else i["titulo"]} for i in itens]
    corpo = ics(f"Caderneta · {escola.nome if escola else ''}", exibidos)
    return Response(corpo, media_type="text/calendar; charset=utf-8")
