"""Convites de uso único: equipe da escola, responsáveis e alunos. Não existe cadastro aberto."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import mail
from app.audit import registrar
from app.config import get_settings
from app.db import get_db, set_ctx
from app.deps import Contexto, equipe, ip_de, so_admin
from app.models import Aluno, Convite, Escola, Papel, Usuario, UsuarioPerfil, VinculoResponsavel
from app.routers.auth import abre_sessao, estado
from app.security import hash_senha, hash_token, novo_token, senha_fraca, verifica_senha

router = APIRouter(tags=["convites"])

PAPEIS_EQUIPE = {Papel.admin, Papel.coordenacao, Papel.professor}
NOME_PAPEL = {
    Papel.admin: "administração da escola",
    Papel.coordenacao: "coordenação",
    Papel.professor: "professor(a)",
    Papel.responsavel: "responsável",
    Papel.aluno: "aluno(a)",
}


class ConviteEquipeIn(BaseModel):
    email: EmailStr
    nome: str = Field(min_length=2, max_length=200)
    papel: Papel


class AceiteIn(BaseModel):
    nome: str | None = Field(default=None, max_length=200)
    senha: str = Field(max_length=200)


def cria_convite(
    db: Session,
    *,
    escola_id: uuid.UUID,
    email: str,
    nome: str,
    papel: Papel,
    criado_por: uuid.UUID | None,
    vinculo_id: uuid.UUID | None = None,
    aluno_id: uuid.UUID | None = None,
) -> str:
    """Cria o convite, envia o e-mail e devolve o link (útil para a escola mandar por WhatsApp)."""
    s = get_settings()
    token, token_hash = novo_token()
    db.add(
        Convite(
            escola_id=escola_id,
            email=email,
            nome=nome,
            papel=papel,
            vinculo_id=vinculo_id,
            aluno_id=aluno_id,
            token_hash=token_hash,
            expira_em=datetime.now(UTC) + timedelta(days=s.invite_days),
            criado_por=criado_por,
        )
    )
    escola = db.get(Escola, escola_id)
    link = f"{s.public_url}/convite/{token}"
    mail.enviar(
        email,
        f"Convite da {escola.nome if escola else 'escola'} na Caderneta",
        f"Olá, {nome}.\n\nVocê foi convidado(a) como {NOME_PAPEL[papel]} na Caderneta.\n"
        f"Para criar seu acesso, abra o link abaixo (válido por {s.invite_days} dias):\n{link}\n",
    )
    return link


def _convite_valido(db: Session, token: str) -> Convite:
    token_hash = hash_token(token)
    set_ctx(db, convite_token=token_hash)
    c = db.scalar(select(Convite).where(Convite.token_hash == token_hash))
    if not c or c.revogado or c.aceito_em or c.expira_em < datetime.now(UTC):
        raise HTTPException(404, "Convite inválido, já usado ou expirado.")
    set_ctx(db, escola_id=c.escola_id, login_email=c.email)
    return c


@router.post("/convites", status_code=201)
def convida_equipe(dados: ConviteEquipeIn, ctx: Contexto = Depends(so_admin)):
    if dados.papel not in PAPEIS_EQUIPE:
        raise HTTPException(422, "Responsáveis e alunos são convidados pela ficha do aluno.")
    link = cria_convite(
        ctx.db,
        escola_id=ctx.escola_id,
        email=dados.email,
        nome=dados.nome,
        papel=dados.papel,
        criado_por=ctx.usuario.id,
    )
    return {"link": link}


@router.get("/convites")
def lista_convites(ctx: Contexto = Depends(equipe)):
    rows = ctx.db.scalars(
        select(Convite)
        .where(Convite.escola_id == ctx.escola_id, Convite.aceito_em.is_(None), Convite.revogado.is_(False))
        .order_by(Convite.criado_em.desc())
    )
    agora = datetime.now(UTC)
    return [
        {
            "id": c.id,
            "email": c.email,
            "nome": c.nome,
            "papel": c.papel,
            "criado_em": c.criado_em,
            "expirado": c.expira_em < agora,
        }
        for c in rows
    ]


@router.delete("/convites/{convite_id}", status_code=204)
def revoga(convite_id: uuid.UUID, ctx: Contexto = Depends(so_admin)):
    c = ctx.db.get(Convite, convite_id)
    if not c:
        raise HTTPException(404, "Convite não encontrado.")
    c.revogado = True


@router.get("/convites/abrir/{token}")
def ver_convite(token: str, db: Session = Depends(get_db, scope="function")):
    c = _convite_valido(db, token)
    escola = db.get(Escola, c.escola_id)
    aluno = db.get(Aluno, c.aluno_id) if c.aluno_id else None
    existe = db.scalar(select(Usuario.id).where(Usuario.email == c.email)) is not None
    return {
        "nome": c.nome,
        "email": c.email,
        "papel": c.papel,
        "escola": escola.nome if escola else None,
        "aluno": f"{aluno.nome} {aluno.sobrenome}" if aluno else None,
        "conta_existente": existe,
    }


@router.post("/convites/abrir/{token}")
def aceita(
    token: str, dados: AceiteIn, request: Request, response: Response, db: Session = Depends(get_db, scope="function")
):
    c = _convite_valido(db, token)
    usuario = db.scalar(select(Usuario).where(Usuario.email == c.email))
    if usuario:
        # Conta já existe (ex.: professor que também é pai): confirma com a senha atual.
        set_ctx(db, usuario_id=usuario.id)
        if not verifica_senha(usuario.senha_hash, dados.senha):
            return JSONResponse({"detail": "Senha incorreta para a conta existente."}, 401)
    else:
        if erro := senha_fraca(dados.senha):
            raise HTTPException(422, erro)
        usuario = Usuario(id=uuid.uuid4(), email=c.email, nome=(dados.nome or c.nome).strip())
        set_ctx(db, usuario_id=usuario.id)
        usuario.senha_hash = hash_senha(dados.senha)
        db.add(usuario)
        db.flush()

    ja_tem = db.scalar(
        select(UsuarioPerfil).where(
            UsuarioPerfil.usuario_id == usuario.id,
            UsuarioPerfil.escola_id == c.escola_id,
            UsuarioPerfil.papel == c.papel,
        )
    )
    if not ja_tem:
        db.add(UsuarioPerfil(usuario_id=usuario.id, escola_id=c.escola_id, papel=c.papel))
    if c.vinculo_id and (v := db.get(VinculoResponsavel, c.vinculo_id)):
        v.usuario_id = usuario.id
    if c.papel == Papel.aluno and c.aluno_id and (a := db.get(Aluno, c.aluno_id)):
        a.usuario_id = usuario.id
    c.aceito_em = datetime.now(UTC)
    db.flush()
    sessao = abre_sessao(db, request, response, usuario)
    registrar(
        db,
        "convite_aceito",
        escola_id=c.escola_id,
        usuario_id=usuario.id,
        entidade="convite",
        entidade_id=c.id,
        ip=ip_de(request),
    )
    return estado(db, usuario, sessao)
