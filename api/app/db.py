"""Conexão com o banco e contexto de Row-Level Security por transação."""

import uuid
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10)


@lru_cache
def _factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=True)


def set_ctx(db: Session, **values: uuid.UUID | str | None) -> None:
    """Define variáveis `app.*` válidas só nesta transação (lidas pelas políticas RLS)."""
    for key, value in values.items():
        db.execute(
            text("SELECT set_config(:k, :v, true)"),
            {"k": f"app.{key}", "v": "" if value is None else str(value)},
        )


def get_db() -> Iterator[Session]:
    """Uma transação por requisição: commit no fim, rollback em erro.

    Use sempre com `Depends(get_db, scope="function")`: assim o commit acontece ANTES de a resposta
    ser enviada. Com o escopo padrão ("request"), o cliente podia receber a resposta do login e
    chamar a API de novo antes de a sessão existir no banco.
    """
    db = _factory()()
    try:
        with db.begin():
            yield db
    finally:
        db.close()
