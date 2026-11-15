"""Login, 2FA (TOTP), troca de perfil e recuperação de senha."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import mail
from app.audit import registrar
from app.config import get_settings
from app.db import get_db, set_ctx
from app.deps import COOKIE, Contexto, autenticado, ip_de, precisa_2fa, sessao_parcial
from app.models import Escola, Sessao, TokenSenha, Usuario, UsuarioPerfil
from app.security import (
    cifra,
    decifra,
    hash_senha,
    hash_token,
    novo_token,
    novo_totp_secret,
    senha_fraca,
    totp_uri,
    verifica_senha,
    verifica_totp,
)

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FALHAS = 5
ERRO_LOGIN = "E-mail ou senha incorretos."


class LoginIn(BaseModel):
    email: EmailStr
    senha: str = Field(max_length=200)


class CodigoIn(BaseModel):
    codigo: str = Field(min_length=6, max_length=8)


class PerfilIn(BaseModel):
    perfil_id: uuid.UUID


class EsqueciIn(BaseModel):
    email: EmailStr


class RedefinirIn(BaseModel):
    token: str = Field(max_length=100)
    senha: str = Field(max_length=200)


def _registra_falha(db: Session, usuario: Usuario) -> None:
    usuario.falhas_login += 1
    if usuario.falhas_login >= MAX_FALHAS:
        # Bloqueio progressivo: 1, 2, 4, 8... minutos, até 1 hora.
        minutos = min(60, 2 ** (usuario.falhas_login - MAX_FALHAS))
        usuario.bloqueado_ate = datetime.now(UTC) + timedelta(minutes=minutos)


def bloqueado(usuario: Usuario) -> bool:
    return bool(usuario.bloqueado_ate and usuario.bloqueado_ate > datetime.now(UTC))


def perfis_do_usuario(db: Session, usuario_id: uuid.UUID) -> list[UsuarioPerfil]:
    return list(
        db.scalars(select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == usuario_id, UsuarioPerfil.ativo.is_(True)))
    )


def abre_sessao(db: Session, request: Request, response: Response, usuario: Usuario) -> Sessao:
    s = get_settings()
    token, token_hash = novo_token()
    perfis = perfis_do_usuario(db, usuario.id)
    sessao = Sessao(
        token_hash=token_hash,
        usuario_id=usuario.id,
        perfil_id=perfis[0].id if len(perfis) == 1 else None,
        mfa_ok=not usuario.totp_ativo,
        expira_em=datetime.now(UTC) + timedelta(days=s.session_max_days),
        ip=ip_de(request),
        user_agent=(request.headers.get("user-agent") or "")[:300],
    )
    db.add(sessao)
    response.set_cookie(
        COOKIE,
        token,
        max_age=s.session_max_days * 86400,
        httponly=True,
        secure=s.cookie_secure,
        samesite="lax",
        path="/api",
    )
    return sessao


def estado(ctx_db: Session, usuario: Usuario, sessao: Sessao) -> dict:
    perfis = perfis_do_usuario(ctx_db, usuario.id)
    if usuario.totp_ativo and not sessao.mfa_ok:
        return {"status": "codigo"}
    if not usuario.totp_ativo and precisa_2fa(usuario, perfis):
        return {"status": "configurar_2fa"}
    return {"status": "ok"}


@router.post("/login")
def login(dados: LoginIn, request: Request, response: Response, db: Session = Depends(get_db, scope="function")):
    set_ctx(db, login_email=dados.email)
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario:
        set_ctx(db, usuario_id=usuario.id)
        if bloqueado(usuario):
            return JSONResponse({"detail": "Muitas tentativas. Tente de novo em alguns minutos."}, 429)
    ok = verifica_senha(usuario.senha_hash if usuario else None, dados.senha)
    if not usuario or not ok or not usuario.ativo:
        if usuario:
            _registra_falha(db, usuario)
            registrar(db, "login_falhou", escola_id=None, usuario_id=usuario.id, ip=ip_de(request))
        return JSONResponse({"detail": ERRO_LOGIN}, 401)  # sem exceção: o contador de falhas é salvo
    usuario.falhas_login = 0
    usuario.bloqueado_ate = None
    sessao = abre_sessao(db, request, response, usuario)
    registrar(db, "login", escola_id=None, usuario_id=usuario.id, ip=ip_de(request))
    return estado(db, usuario, sessao)


@router.post("/codigo")
def confirma_codigo(dados: CodigoIn, request: Request, ctx: Contexto = Depends(sessao_parcial)):
    u = ctx.usuario
    if not u.totp_ativo or not u.totp_secret_enc:
        raise HTTPException(400, "Verificação em duas etapas não está ativa.")
    if bloqueado(u):
        return JSONResponse({"detail": "Muitas tentativas. Tente de novo em alguns minutos."}, 429)
    if not verifica_totp(decifra(u.totp_secret_enc, str(u.id)), dados.codigo):
        _registra_falha(ctx.db, u)
        return JSONResponse({"detail": "Código inválido."}, 401)
    u.falhas_login = 0
    ctx.sessao.mfa_ok = True
    return estado(ctx.db, u, ctx.sessao)


@router.post("/2fa/iniciar")
def inicia_2fa(ctx: Contexto = Depends(sessao_parcial)):
    u = ctx.usuario
    if u.totp_ativo:
        raise HTTPException(400, "A verificação em duas etapas já está ativa.")
    secret = novo_totp_secret()
    u.totp_secret_enc = cifra(secret, str(u.id))
    return {"secret": secret, "uri": totp_uri(secret, u.email)}


@router.post("/2fa/ativar")
def ativa_2fa(dados: CodigoIn, request: Request, ctx: Contexto = Depends(sessao_parcial)):
    u = ctx.usuario
    if u.totp_ativo or not u.totp_secret_enc:
        raise HTTPException(400, "Inicie a configuração primeiro.")
    if not verifica_totp(decifra(u.totp_secret_enc, str(u.id)), dados.codigo):
        return JSONResponse({"detail": "Código inválido. Confira o horário do celular."}, 400)
    u.totp_ativo = True
    ctx.sessao.mfa_ok = True
    registrar(ctx.db, "2fa_ativado", escola_id=None, usuario_id=u.id, ip=ip_de(request))
    return estado(ctx.db, u, ctx.sessao)


@router.get("/me")
def me(ctx: Contexto = Depends(sessao_parcial)):
    perfis = ctx.db.execute(
        select(UsuarioPerfil, Escola.nome)
        .join(Escola, Escola.id == UsuarioPerfil.escola_id)
        .where(UsuarioPerfil.usuario_id == ctx.usuario.id, UsuarioPerfil.ativo.is_(True))
        .order_by(Escola.nome, UsuarioPerfil.papel)
    ).all()
    u = ctx.usuario
    return {
        **estado(ctx.db, u, ctx.sessao),
        "usuario": {"id": u.id, "nome": u.nome, "email": u.email, "totp_ativo": u.totp_ativo},
        "perfis": [{"id": p.id, "papel": p.papel, "escola_id": p.escola_id, "escola": nome} for p, nome in perfis],
        "perfil_ativo": ctx.perfil.id if ctx.perfil else None,
    }


@router.post("/perfil")
def escolhe_perfil(dados: PerfilIn, ctx: Contexto = Depends(autenticado)):
    perfil = ctx.db.get(UsuarioPerfil, dados.perfil_id)
    if not perfil or perfil.usuario_id != ctx.usuario.id or not perfil.ativo:
        raise HTTPException(404, "Perfil não encontrado.")
    ctx.sessao.perfil_id = perfil.id
    return {"perfil_ativo": perfil.id}


@router.post("/logout", status_code=204)
def logout(response: Response, ctx: Contexto = Depends(sessao_parcial)):
    ctx.db.delete(ctx.sessao)
    response.delete_cookie(COOKIE, path="/api")


@router.post("/senha/esqueci", status_code=204)
def esqueci(dados: EsqueciIn, db: Session = Depends(get_db, scope="function")):
    """Sempre 204: não revela se o e-mail existe."""
    set_ctx(db, login_email=dados.email)
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email, Usuario.ativo.is_(True)))
    if not usuario or not usuario.senha_hash:
        return
    token, token_hash = novo_token()
    db.add(TokenSenha(usuario_id=usuario.id, token_hash=token_hash, expira_em=datetime.now(UTC) + timedelta(hours=1)))
    link = f"{get_settings().public_url}/redefinir-senha?token={token}"
    mail.enviar(
        usuario.email,
        "Caderneta: redefinição de senha",
        f"Olá, {usuario.nome}.\n\nPara criar uma nova senha, acesse (válido por 1 hora):\n{link}\n\n"
        "Se você não pediu, ignore este e-mail.",
    )


@router.post("/senha/redefinir", status_code=204)
def redefinir(dados: RedefinirIn, request: Request, db: Session = Depends(get_db, scope="function")):
    tk = db.scalar(select(TokenSenha).where(TokenSenha.token_hash == hash_token(dados.token)))
    if not tk or tk.usado_em or tk.expira_em < datetime.now(UTC):
        raise HTTPException(400, "Link inválido ou expirado. Peça um novo.")
    if erro := senha_fraca(dados.senha):
        raise HTTPException(422, erro)
    set_ctx(db, usuario_id=tk.usuario_id)
    usuario = db.get(Usuario, tk.usuario_id)
    assert usuario is not None
    usuario.senha_hash = hash_senha(dados.senha)
    usuario.falhas_login = 0
    usuario.bloqueado_ate = None
    tk.usado_em = datetime.now(UTC)
    db.execute(delete(Sessao).where(Sessao.usuario_id == usuario.id))  # derruba sessões antigas
    registrar(db, "senha_redefinida", escola_id=None, usuario_id=usuario.id, ip=ip_de(request))
