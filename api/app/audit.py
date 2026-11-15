"""Registro de auditoria (tabela só de inserção)."""

import uuid

from sqlalchemy.orm import Session

from app.models import Auditoria


def registrar(
    db: Session,
    acao: str,
    *,
    escola_id: uuid.UUID | None,
    usuario_id: uuid.UUID | None,
    entidade: str | None = None,
    entidade_id: object = None,
    detalhes: dict | None = None,
    ip: str | None = None,
) -> None:
    db.add(
        Auditoria(
            escola_id=escola_id,
            usuario_id=usuario_id,
            acao=acao,
            entidade=entidade,
            entidade_id=str(entidade_id) if entidade_id is not None else None,
            detalhes=detalhes,
            ip=ip,
        )
    )
