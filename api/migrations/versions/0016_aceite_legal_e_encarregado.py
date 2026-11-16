"""aceite versionado de politica de privacidade e termos; encarregado (DPO) da escola

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("escola", sa.Column("encarregado_nome", sa.String(200), nullable=True))
    op.add_column("escola", sa.Column("encarregado_email", sa.String(200), nullable=True))
    op.create_table(
        "aceite_legal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("doc", sa.String(20), nullable=False),
        sa.Column("versao", sa.String(40), nullable=False),
        sa.Column("aceito_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "doc", "versao"),
    )
    op.create_index("ix_aceite_legal_usuario_id", "aceite_legal", ["usuario_id"])
    op.execute("GRANT SELECT, INSERT ON aceite_legal TO caderneta_app")
    op.execute("ALTER TABLE aceite_legal ENABLE ROW LEVEL SECURITY")
    # cada pessoa só enxerga e registra o próprio aceite
    op.execute(
        "CREATE POLICY propria ON aceite_legal USING (usuario_id = app_usuario()) WITH CHECK (usuario_id = app_usuario())"
    )


def downgrade() -> None:
    op.drop_table("aceite_legal")
    op.drop_column("escola", "encarregado_email")
    op.drop_column("escola", "encarregado_nome")
