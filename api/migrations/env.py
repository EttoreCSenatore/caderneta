"""Migrações rodam com o papel DONO (CADERNETA_OWNER_DATABASE_URL), nunca com o papel da API."""

from alembic import context
from sqlalchemy import create_engine

from app.config import get_settings
from app.models import Base

target_metadata = Base.metadata


def run() -> None:
    url = context.config.attributes.get("url") or get_settings().owner_database_url
    if context.is_offline_mode():
        # `alembic upgrade A:B --sql`: só imprime o SQL, sem conectar (relatório de migrations no PR, MO.5)
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(url)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


run()
