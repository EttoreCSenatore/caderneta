"""Provas, trabalhos e fila de impressão.

Fluxo: rascunho → enviada → (ajustes ↔ enviada) → aprovada → impressa. A aprovação da coordenação é opcional
(configuração da escola). Provas são sigilosas: só o autor, a coordenação e a secretaria (admin) acessam o arquivo;
famílias e alunos só veem o que o professor publicar, e uma prova só pode ser publicada a partir da data de aplicação.
Downloads usam link assinado de curta duração e ficam na auditoria.
"""

import uuid
from datetime import UTC, date, datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from app import arquivos
from app.audit import registrar
from app.config import get_settings
from app.deps import Contexto, com_perfil, so_admin
from app.models import (
    STAFF,
    Arquivo,
    Atribuicao,
    Escola,
    Papel,
    PedidoComentario,
    PedidoImpressao,
    StatusPedido,
    TipoPedido,
    Turma,
)
from app.notificacoes import alunos_do_publico, equipe_da_escola, familia_dos_alunos, notificar
from app.regras import atribuicao_do_diario, matriculas_da_turma
from app.routers.turmas import turmas_visiveis
from app.security import assina_link, verifica_link

router = APIRouter(tags=["impressao"])
EDITAVEIS = {StatusPedido.rascunho, StatusPedido.ajustes}
LEITORES = {Papel.responsavel, Papel.aluno}


class ConfigIn(BaseModel):
    aprovacao: bool
    reserva_copias: int = Field(ge=0, le=50)
    antecedencia_dias: int = Field(ge=0, le=30)


class PedidoEdit(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    data_aplicacao: date | None = None
    copias: int | None = Field(default=None, ge=1, le=1000)
    copias_adaptadas: int | None = Field(default=None, ge=0, le=100)
    frente_verso: bool | None = None
    colorido: bool | None = None
    grampear: bool | None = None
    observacoes: str | None = Field(default=None, max_length=500)


class ComentarioIn(BaseModel):
    corpo: str = Field(min_length=1, max_length=1000)


class PublicarIn(BaseModel):
    publicado: bool


# --- Acesso -------------------------------------------------------------------------------------------------


def _escola(ctx: Contexto) -> Escola:
    e = ctx.db.get(Escola, ctx.escola_id)
    assert e is not None
    return e


def _pedido(ctx: Contexto, pedido_id: uuid.UUID, *, escrita: bool = False) -> PedidoImpressao:
    """Equipe vê todos; professor, os seus; famílias e alunos, só os publicados das turmas deles (leitura)."""
    p = ctx.db.get(PedidoImpressao, pedido_id)
    ok = p is not None
    if ok and ctx.papel not in STAFF:
        if ctx.papel == Papel.professor:
            ok = p.autor_id == ctx.usuario.id
        else:
            ok = not escrita and p.publicado and p.atribuicao.turma_id in set(ctx.db.scalars(turmas_visiveis(ctx)))
    if not ok:
        raise HTTPException(404, "Pedido não encontrado.")
    return p


def _nome_prof(p: PedidoImpressao) -> str:
    return p.atribuicao.professor.nome


def pedido_out(ctx: Contexto, p: PedidoImpressao, detalhe: bool = False) -> dict:
    turma = ctx.db.get(Turma, p.atribuicao.turma_id)
    hoje = datetime.now(UTC).date()
    visao_familia = ctx.papel in LEITORES
    out = {
        "id": p.id,
        "tipo": p.tipo,
        "titulo": p.titulo,
        "turma": turma.nome if turma else None,
        "turma_id": p.atribuicao.turma_id,
        "atribuicao_id": p.atribuicao_id,
        "disciplina": p.atribuicao.disciplina.nome,
        "professor": _nome_prof(p),
        "data_aplicacao": p.data_aplicacao,
        "status": p.status,
        "publicado": p.publicado,
        "arquivo": {"nome": p.arquivo.nome, "tamanho": p.arquivo.tamanho, "mime": p.arquivo.mime},
    }
    if visao_familia:
        return out
    out |= {
        "autor_id": p.autor_id,
        "copias": p.copias,
        "copias_calculadas": p.copias_calculadas,
        "copias_adaptadas": p.copias_adaptadas,
        "frente_verso": p.frente_verso,
        "colorido": p.colorido,
        "grampear": p.grampear,
        "observacoes": p.observacoes,
        "adaptado": (
            {"nome": p.arquivo_adaptado.nome, "tamanho": p.arquivo_adaptado.tamanho} if p.arquivo_adaptado else None
        ),
        "enviado_em": p.enviado_em,
        "impresso_em": p.impresso_em,
        "atrasado": p.status in {StatusPedido.rascunho, StatusPedido.ajustes, StatusPedido.enviada}
        and (p.data_aplicacao - hoje).days < _escola(ctx).antecedencia_dias,
    }
    if detalhe:
        out["comentarios"] = [
            {"id": c.id, "autor": c.autor.nome if c.autor else None, "corpo": c.corpo, "criado_em": c.criado_em}
            for c in ctx.db.scalars(
                select(PedidoComentario).where(PedidoComentario.pedido_id == p.id).order_by(PedidoComentario.criado_em)
            )
        ]
    return out


def _alunos_da_turma(ctx: Contexto, turma: Turma) -> int:
    return len(matriculas_da_turma(ctx, turma))


# --- Configuração -------------------------------------------------------------------------------------------


@router.get("/impressao/config")
def ver_config(ctx: Contexto = Depends(com_perfil)):
    if ctx.papel in LEITORES:
        raise HTTPException(403, "Sem permissão para esta ação.")
    e = _escola(ctx)
    return {
        "aprovacao": e.aprovacao_impressao,
        "reserva_copias": e.reserva_copias,
        "antecedencia_dias": e.antecedencia_dias,
    }


@router.put("/impressao/config")
def salvar_config(body: ConfigIn, ctx: Contexto = Depends(so_admin)):
    e = _escola(ctx)
    e.aprovacao_impressao, e.reserva_copias, e.antecedencia_dias = (
        body.aprovacao,
        body.reserva_copias,
        body.antecedencia_dias,
    )
    registrar(
        ctx.db, "impressao.config", escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, detalhes=body.model_dump()
    )
    return ver_config(ctx)


@router.get("/atribuicoes/{atribuicao_id}/copias-sugeridas")
def copias_sugeridas(atribuicao_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    if ctx.papel in LEITORES:
        raise HTTPException(403, "Sem permissão para esta ação.")
    _, turma = atribuicao_do_diario(ctx, atribuicao_id)
    alunos, reserva = _alunos_da_turma(ctx, turma), _escola(ctx).reserva_copias
    return {"alunos": alunos, "reserva": reserva, "total": alunos + reserva}


# --- Criação e edição ---------------------------------------------------------------------------------------


async def _ler(arq: UploadFile) -> bytes:
    dados = await arq.read(get_settings().max_arquivo_bytes + 1)
    return dados


@router.post("/pedidos", status_code=201)
async def criar(
    titulo: str = Form(min_length=1, max_length=200),
    tipo: TipoPedido = Form(),
    data_aplicacao: date = Form(),
    atribuicao_ids: list[uuid.UUID] = Form(min_length=1, max_length=10),
    copias: int | None = Form(default=None, ge=1, le=1000),
    copias_adaptadas: int = Form(default=0, ge=0, le=100),
    frente_verso: bool = Form(default=True),
    colorido: bool = Form(default=False),
    grampear: bool = Form(default=False),
    observacoes: str | None = Form(default=None, max_length=500),
    arquivo: UploadFile = File(),
    arquivo_adaptado: UploadFile | None = File(default=None),
    ctx: Contexto = Depends(com_perfil),
):
    """Cria um pedido por turma (o mesmo arquivo serve a todas). Começa como rascunho."""
    if ctx.papel in LEITORES:
        raise HTTPException(403, "Sem permissão para esta ação.")
    if data_aplicacao < datetime.now(UTC).date():
        raise HTTPException(422, "A data de aplicação não pode ser no passado.")
    atribs = [atribuicao_do_diario(ctx, i) for i in dict.fromkeys(atribuicao_ids)]
    principal = arquivos.grava(
        ctx.db, escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, nome=arquivo.filename, dados=await _ler(arquivo)
    )
    adaptado = None
    if arquivo_adaptado is not None and arquivo_adaptado.filename:
        adaptado = arquivos.grava(
            ctx.db,
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            nome=arquivo_adaptado.filename,
            dados=await _ler(arquivo_adaptado),
        )
    reserva = _escola(ctx).reserva_copias
    criados = []
    for a, turma in atribs:
        calculadas = _alunos_da_turma(ctx, turma) + reserva
        p = PedidoImpressao(
            escola_id=ctx.escola_id,
            autor_id=ctx.usuario.id,
            atribuicao_id=a.id,
            arquivo_id=principal.id,
            arquivo_adaptado_id=adaptado.id if adaptado else None,
            tipo=tipo,
            titulo=titulo.strip(),
            data_aplicacao=data_aplicacao,
            copias=copias or calculadas,
            copias_calculadas=calculadas,
            copias_adaptadas=copias_adaptadas if adaptado else 0,
            frente_verso=frente_verso,
            colorido=colorido,
            grampear=grampear,
            observacoes=(observacoes or "").strip() or None,
        )
        ctx.db.add(p)
        criados.append(p)
    ctx.db.flush()
    for p in criados:
        registrar(
            ctx.db,
            "pedido.criar",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="pedido",
            entidade_id=p.id,
        )
    ctx.db.refresh(criados[0])
    return [pedido_out(ctx, p, True) for p in criados]


@router.post("/pedidos/{pedido_id}/arquivo")
async def trocar_arquivo(
    pedido_id: uuid.UUID,
    versao: str = Form(default="principal", pattern="^(principal|adaptado)$"),
    arquivo: UploadFile = File(),
    ctx: Contexto = Depends(com_perfil),
):
    """Troca o arquivo (ex.: depois de um pedido de ajustes). O arquivo antigo é apagado se ninguém mais o usa."""
    p = _pedido(ctx, pedido_id, escrita=True)
    _pode_editar(ctx, p)
    novo = arquivos.grava(
        ctx.db, escola_id=ctx.escola_id, usuario_id=ctx.usuario.id, nome=arquivo.filename, dados=await _ler(arquivo)
    )
    antigo = p.arquivo if versao == "principal" else p.arquivo_adaptado
    if versao == "principal":
        p.arquivo_id = novo.id
    else:
        p.arquivo_adaptado_id = novo.id
    ctx.db.flush()
    if antigo:
        _descarta_se_orfao(ctx, antigo)
    registrar(
        ctx.db,
        "pedido.arquivo",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="pedido",
        entidade_id=p.id,
    )
    ctx.db.refresh(p)
    return pedido_out(ctx, p, True)


def _descarta_se_orfao(ctx: Contexto, a: Arquivo) -> None:
    usado = ctx.db.scalar(
        select(PedidoImpressao.id)
        .where((PedidoImpressao.arquivo_id == a.id) | (PedidoImpressao.arquivo_adaptado_id == a.id))
        .limit(1)
    )
    if not usado:
        arquivos.apaga(a)
        ctx.db.delete(a)


def _pode_editar(ctx: Contexto, p: PedidoImpressao) -> None:
    autor = p.autor_id == ctx.usuario.id and p.status in EDITAVEIS
    secretaria = ctx.papel == Papel.admin and p.status != StatusPedido.impressa
    if not (autor or secretaria):
        raise HTTPException(409, "Este pedido não pode mais ser alterado.")


@router.patch("/pedidos/{pedido_id}")
def editar(pedido_id: uuid.UUID, body: PedidoEdit, ctx: Contexto = Depends(com_perfil)):
    p = _pedido(ctx, pedido_id, escrita=True)
    _pode_editar(ctx, p)
    dados = body.model_dump(exclude_unset=True)
    if "data_aplicacao" in dados and dados["data_aplicacao"] < datetime.now(UTC).date():
        raise HTTPException(422, "A data de aplicação não pode ser no passado.")
    for k, v in dados.items():
        if k == "titulo" and v is None:
            continue
        setattr(p, k, v)
    if "copias_adaptadas" in dados and not p.arquivo_adaptado_id:
        p.copias_adaptadas = 0
    _auditar(ctx, "pedido.editar", p)
    return pedido_out(ctx, p, True)


@router.delete("/pedidos/{pedido_id}", status_code=204)
def excluir(pedido_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    p = _pedido(ctx, pedido_id, escrita=True)
    if not (p.autor_id == ctx.usuario.id and p.status == StatusPedido.rascunho):
        raise HTTPException(409, "Só rascunhos podem ser excluídos.")
    antigos = [a for a in (p.arquivo, p.arquivo_adaptado) if a]
    registrar(
        ctx.db,
        "pedido.excluir",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="pedido",
        entidade_id=p.id,
    )
    ctx.db.delete(p)
    ctx.db.flush()
    for a in antigos:
        _descarta_se_orfao(ctx, a)


# --- Listagem -----------------------------------------------------------------------------------------------


@router.get("/pedidos")
def listar(
    status: StatusPedido | None = None,
    de: date | None = None,
    ate: date | None = None,
    turma_id: uuid.UUID | None = None,
    ctx: Contexto = Depends(com_perfil),
):
    """Fila: equipe vê todos; professor, os seus; famílias e alunos, só os publicados das turmas deles."""
    q = select(PedidoImpressao).order_by(PedidoImpressao.data_aplicacao, PedidoImpressao.criado_em).limit(300)
    if ctx.papel == Papel.professor:
        q = q.where(PedidoImpressao.autor_id == ctx.usuario.id)
    elif ctx.papel in LEITORES:
        q = q.where(
            PedidoImpressao.publicado.is_(True),
            PedidoImpressao.atribuicao_id.in_(
                select(Atribuicao.id).where(Atribuicao.turma_id.in_(turmas_visiveis(ctx)))
            ),
        )
    if status:
        q = q.where(PedidoImpressao.status == status)
    if de:
        q = q.where(PedidoImpressao.data_aplicacao >= de)
    if ate:
        q = q.where(PedidoImpressao.data_aplicacao <= ate)
    if turma_id:
        q = q.where(PedidoImpressao.atribuicao_id.in_(select(Atribuicao.id).where(Atribuicao.turma_id == turma_id)))
    return [pedido_out(ctx, p) for p in ctx.db.scalars(q)]


@router.get("/pedidos/{pedido_id}")
def ver(pedido_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    return pedido_out(ctx, _pedido(ctx, pedido_id), True)


# --- Fluxo --------------------------------------------------------------------------------------------------


def _avisa(ctx: Contexto, usuarios, titulo: str, p: PedidoImpressao) -> None:
    notificar(
        ctx.db,
        escola_id=ctx.escola_id,
        usuarios=usuarios,
        tipo="impressao",
        titulo=titulo,
        corpo=f"{p.titulo} · {p.atribuicao.disciplina.nome}",
        url="/provas",
        excluir=ctx.usuario.id,
    )


def _admins(ctx: Contexto) -> set[uuid.UUID]:
    from app.models import UsuarioPerfil

    return set(
        ctx.db.scalars(
            select(UsuarioPerfil.usuario_id).where(
                UsuarioPerfil.escola_id == ctx.escola_id,
                UsuarioPerfil.ativo.is_(True),
                UsuarioPerfil.papel == Papel.admin,
            )
        )
    )


def _auditar(ctx: Contexto, acao: str, p: PedidoImpressao, **detalhes) -> None:
    registrar(
        ctx.db,
        acao,
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="pedido",
        entidade_id=p.id,
        detalhes=detalhes or None,
    )


@router.post("/pedidos/{pedido_id}/enviar")
def enviar(pedido_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    p = _pedido(ctx, pedido_id, escrita=True)
    if p.status not in EDITAVEIS or not (p.autor_id == ctx.usuario.id or ctx.papel == Papel.admin):
        raise HTTPException(409, "Este pedido não pode ser enviado agora.")
    e = _escola(ctx)
    hoje = datetime.now(UTC).date()
    if ctx.papel != Papel.admin and (p.data_aplicacao - hoje).days < e.antecedencia_dias:
        raise HTTPException(
            409,
            f"A escola exige {e.antecedencia_dias} dia(s) de antecedência. Fale com a direção para um pedido urgente.",
        )
    agora = datetime.now(UTC)
    p.enviado_em = agora
    if e.aprovacao_impressao:
        p.status = StatusPedido.enviada
        _avisa(ctx, equipe_da_escola(ctx.db, ctx.escola_id), "Pedido de impressão para revisar", p)
    else:
        p.status = StatusPedido.aprovada
        p.aprovado_em = agora
        _avisa(ctx, _admins(ctx), "Novo pedido na fila de impressão", p)
    _auditar(ctx, "pedido.enviar", p, status=p.status.value)
    return pedido_out(ctx, p, True)


def _revisor(ctx: Contexto, p: PedidoImpressao, de: StatusPedido) -> None:
    if ctx.papel not in STAFF:
        raise HTTPException(403, "Sem permissão para esta ação.")
    if p.status != de:
        raise HTTPException(409, f'O pedido está "{p.status.value}" e não pode seguir por aqui.')


@router.post("/pedidos/{pedido_id}/aprovar")
def aprovar(pedido_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    p = _pedido(ctx, pedido_id)
    _revisor(ctx, p, StatusPedido.enviada)
    p.status, p.aprovado_por, p.aprovado_em = StatusPedido.aprovada, ctx.usuario.id, datetime.now(UTC)
    _avisa(ctx, ({p.autor_id} if p.autor_id else set()) | _admins(ctx), "Pedido de impressão aprovado", p)
    _auditar(ctx, "pedido.aprovar", p)
    return pedido_out(ctx, p, True)


@router.post("/pedidos/{pedido_id}/ajustes")
def pedir_ajustes(pedido_id: uuid.UUID, body: ComentarioIn, ctx: Contexto = Depends(com_perfil)):
    p = _pedido(ctx, pedido_id)
    _revisor(ctx, p, StatusPedido.enviada)
    p.status = StatusPedido.ajustes
    ctx.db.add(
        PedidoComentario(escola_id=ctx.escola_id, pedido_id=p.id, autor_id=ctx.usuario.id, corpo=body.corpo.strip())
    )
    if p.autor_id:
        _avisa(ctx, {p.autor_id}, "Ajustes pedidos no seu pedido de impressão", p)
    _auditar(ctx, "pedido.ajustes", p)
    ctx.db.flush()
    return pedido_out(ctx, p, True)


@router.post("/pedidos/{pedido_id}/imprimir")
def imprimir(pedido_id: uuid.UUID, ctx: Contexto = Depends(so_admin)):
    p = _pedido(ctx, pedido_id)
    if p.status != StatusPedido.aprovada:
        raise HTTPException(409, "Só pedidos aprovados podem ser marcados como impressos.")
    p.status, p.impresso_por, p.impresso_em = StatusPedido.impressa, ctx.usuario.id, datetime.now(UTC)
    if p.autor_id:
        _avisa(ctx, {p.autor_id}, "Seu material foi impresso", p)
    _auditar(ctx, "pedido.imprimir", p, copias=p.copias, adaptadas=p.copias_adaptadas)
    return pedido_out(ctx, p, True)


@router.post("/pedidos/{pedido_id}/comentarios", status_code=201)
def comentar(pedido_id: uuid.UUID, body: ComentarioIn, ctx: Contexto = Depends(com_perfil)):
    p = _pedido(ctx, pedido_id, escrita=True)
    c = PedidoComentario(escola_id=ctx.escola_id, pedido_id=p.id, autor_id=ctx.usuario.id, corpo=body.corpo.strip())
    ctx.db.add(c)
    outros = {p.autor_id} if p.autor_id else set()
    if ctx.papel == Papel.professor:
        outros |= equipe_da_escola(ctx.db, ctx.escola_id)
    _avisa(ctx, outros, "Novo comentário em pedido de impressão", p)
    ctx.db.flush()
    return {"id": c.id, "autor": ctx.usuario.nome, "corpo": c.corpo, "criado_em": c.criado_em}


@router.post("/pedidos/{pedido_id}/publicar")
def publicar(pedido_id: uuid.UUID, body: PublicarIn, ctx: Contexto = Depends(com_perfil)):
    """Mostra o arquivo à turma (enunciado, gabarito). Prova só a partir da data de aplicação."""
    p = _pedido(ctx, pedido_id, escrita=True)
    if not (p.autor_id == ctx.usuario.id or ctx.papel in STAFF):
        raise HTTPException(404, "Pedido não encontrado.")
    if body.publicado:
        if p.status not in {StatusPedido.aprovada, StatusPedido.impressa}:
            raise HTTPException(409, "Só pedidos aprovados podem ser publicados.")
        if p.tipo == TipoPedido.prova and datetime.now(UTC).date() < p.data_aplicacao:
            raise HTTPException(409, "Provas só podem ser publicadas a partir da data de aplicação.")
    mudou = p.publicado != body.publicado
    p.publicado = body.publicado
    if mudou and body.publicado:
        familia = familia_dos_alunos(
            ctx.db, ctx.escola_id, alunos_do_publico(ctx.db, ctx.escola_id, p.atribuicao.turma_id), incluir_alunos=True
        )
        notificar(
            ctx.db,
            escola_id=ctx.escola_id,
            usuarios=familia,
            tipo="material",
            titulo="Novo material publicado",
            corpo=f"{p.titulo} · {p.atribuicao.disciplina.nome}",
            url="/provas",
            excluir=ctx.usuario.id,
        )
    _auditar(ctx, "pedido.publicar", p, publicado=body.publicado)
    return pedido_out(ctx, p, True)


# --- Download por link assinado -----------------------------------------------------------------------------


@router.post("/pedidos/{pedido_id}/arquivo-link")
def link(pedido_id: uuid.UUID, versao: str = "principal", ctx: Contexto = Depends(com_perfil)):
    """Gera um link de curta duração, ligado a este usuário. O download é auditado."""
    p = _pedido(ctx, pedido_id)
    if versao not in {"principal", "adaptado"} or (
        versao == "adaptado" and (not p.arquivo_adaptado or ctx.papel in LEITORES)
    ):
        raise HTTPException(404, "Arquivo não encontrado.")
    ttl = get_settings().link_validade_s
    token = assina_link({"p": str(p.id), "v": versao, "u": str(ctx.usuario.id), "s": str(ctx.escola_id)}, ttl)
    return {"url": f"/api/arquivos/{token}", "expira_em_s": ttl}


@router.get("/arquivos/{token}")
def baixar(token: str, ctx: Contexto = Depends(com_perfil)):
    carga = verifica_link(token)
    if not carga or carga.get("u") != str(ctx.usuario.id) or carga.get("s") != str(ctx.escola_id):
        raise HTTPException(404, "Link inválido ou expirado.")
    p = _pedido(ctx, uuid.UUID(carga["p"]))  # confere o acesso de novo, na hora do download
    a = p.arquivo_adaptado if carga["v"] == "adaptado" else p.arquivo
    if not a or (carga["v"] == "adaptado" and ctx.papel in LEITORES):
        raise HTTPException(404, "Arquivo não encontrado.")
    dados = arquivos.le(a)
    _auditar(ctx, "pedido.baixar", p, versao=carga["v"], arquivo=str(a.id))
    return Response(
        dados,
        media_type=a.mime,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(a.nome)}", "Cache-Control": "no-store"},
    )
