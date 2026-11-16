"""anexos de mensagens

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mensagem_anexo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("mensagem_id", sa.Uuid(), nullable=False),
        sa.Column("arquivo_id", sa.Uuid(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["arquivo_id"], ["arquivo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mensagem_id"], ["mensagem.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ("escola_id", "mensagem_id", "arquivo_id", "criado_em"):
        op.create_index(op.f(f"ix_mensagem_anexo_{c}"), "mensagem_anexo", [c])
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON mensagem_anexo TO caderneta_app")
    op.execute("ALTER TABLE mensagem_anexo ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY isolamento ON mensagem_anexo USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
    )


def downgrade() -> None:
    op.drop_table("mensagem_anexo")
