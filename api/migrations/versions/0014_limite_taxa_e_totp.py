"""limite de taxa (contador por janela) e passo do TOTP já usado (anti-reuso)

Revision ID: 0014
Revises: 0013
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "limite_taxa",
        sa.Column("chave", sa.String(100), primary_key=True),
        sa.Column("janela", sa.BigInteger(), primary_key=True),
        sa.Column("n", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON limite_taxa TO caderneta_app")
    op.add_column("usuario", sa.Column("totp_ultimo_passo", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "totp_ultimo_passo")
    op.drop_table("limite_taxa")
