"""Autenticação por sessão, perfil ativo e checagens de permissão.

Duas camadas: estas funções checam papel e vínculo; o PostgreSQL (RLS) garante que nada de outra
escola aparece, mesmo se uma checagem aqui falhar.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db, set_ctx
from app.models import (
    STAFF,
    Aluno,
    Atribuicao,
    Matricula,
    Papel,
    Sessao,
    Turma,
    Usuario,
    UsuarioPerfil,
    VinculoResponsavel,
)
from app.security import hash_token

COOKIE = "cad_session"


@dataclass
class Contexto:
    db: Session
    sessao: Sessao
    usuario: Usuario
    perfil: UsuarioPerfil | None

    @property
    def escola_id(self) -> uuid.UUID:
        if not self.perfil:
            raise HTTPException(409, "Selecione um perfil")
        return self.perfil.escola_id

    @property
    def papel(self) -> Papel:
        if not self.perfil:
            raise HTTPException(409, "Selecione um perfil")
        return self.perfil.papel


def ip_de(request: Request) -> str | None:
    return request.client.host if request.client else None


def _carrega_sessao(request: Request, db: Session) -> tuple[Sessao, Usuario] | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == hash_token(token)))
    agora = datetime.now(UTC)
    s = get_settings()
    if not sessao or sessao.expira_em < agora or sessao.ultimo_uso < agora - timedelta(hours=s.session_idle_hours):
        return None
    set_ctx(db, usuario_id=sessao.usuario_id)
    usuario = db.get(Usuario, sessao.usuario_id)
    if not usuario or not usuario.ativo:
        return None
    if agora - sessao.ultimo_uso > timedelta(minutes=5):
        sessao.ultimo_uso = agora
    return sessao, usuario


def precisa_2fa(usuario: Usuario, perfis: list[UsuarioPerfil]) -> bool:
    """Equipe da escola (direção, secretaria, coordenação) precisa de 2FA."""
    return get_settings().require_staff_2fa and any(p.papel in STAFF for p in perfis)


def sessao_parcial(request: Request, db: Session = Depends(get_db, scope="function")) -> Contexto:
    """Sessão válida, mesmo sem 2FA concluído. Só para rotas de 2FA, /me e logout."""
    carregada = _carrega_sessao(request, db)
    if not carregada:
        raise HTTPException(401, "Sessão expirada. Entre novamente.")
    sessao, usuario = carregada
    perfil = None
    if sessao.perfil_id:
        perfil = db.get(UsuarioPerfil, sessao.perfil_id)
        if perfil and perfil.ativo:
            set_ctx(db, escola_id=perfil.escola_id)
        else:
            perfil = None
    return Contexto(db, sessao, usuario, perfil)


def autenticado(ctx: Contexto = Depends(sessao_parcial)) -> Contexto:
    if ctx.usuario.totp_ativo and not ctx.sessao.mfa_ok:
        raise HTTPException(401, "Confirme o código de verificação.")
    if not ctx.usuario.totp_ativo:
        perfis = list(ctx.db.scalars(select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == ctx.usuario.id)))
        if precisa_2fa(ctx.usuario, perfis):
            raise HTTPException(403, "Configure a verificação em duas etapas para continuar.")
    return ctx


def com_perfil(ctx: Contexto = Depends(autenticado)) -> Contexto:
    _ = ctx.escola_id  # 409 se não houver perfil ativo
    return ctx


def exige(*papeis: Papel):
    def dep(ctx: Contexto = Depends(com_perfil)) -> Contexto:
        if ctx.papel not in papeis:
            raise HTTPException(403, "Sem permissão para esta ação.")
        return ctx

    return dep


so_admin = exige(Papel.admin)
equipe = exige(Papel.admin, Papel.coordenacao)
equipe_ou_professor = exige(Papel.admin, Papel.coordenacao, Papel.professor)


# --- Escopo de alunos por papel -------------------------------------------------------------------------


def ids_alunos_visiveis(ctx: Contexto):
    """Subconsulta com os ids de alunos que o perfil ativo pode ver (None = todos da escola)."""
    papel = ctx.papel
    if papel in STAFF:
        return None
    if papel == Papel.professor:
        return (
            select(Matricula.aluno_id)
            .join(Turma, Turma.id == Matricula.turma_id)
            .join(Atribuicao, Atribuicao.turma_id == Turma.id)
            .where(Atribuicao.professor_id == ctx.usuario.id)
        )
    if papel == Papel.responsavel:
        return select(VinculoResponsavel.aluno_id).where(
            VinculoResponsavel.usuario_id == ctx.usuario.id, VinculoResponsavel.restrito.is_(False)
        )
    return select(Aluno.id).where(Aluno.usuario_id == ctx.usuario.id)


def aluno_visivel(ctx: Contexto, aluno_id: uuid.UUID) -> Aluno:
    """404 tanto para inexistente quanto para sem acesso (não revela existência)."""
    q = select(Aluno).where(Aluno.id == aluno_id)
    escopo = ids_alunos_visiveis(ctx)
    if escopo is not None:
        q = q.where(Aluno.id.in_(escopo))
    aluno = ctx.db.scalar(q)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado.")
    return aluno
