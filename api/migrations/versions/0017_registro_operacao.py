"""registro de operação: backups e testes de restauração (MO.4)

Revision ID: 0017
Revises: 0016
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Da instalação, não de uma escola: sem escola_id e sem dado pessoal. O app só lê; quem grava é o CLI (dono).
    op.create_table(
        "registro_operacao",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("feito_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("detalhe", sa.String(200), nullable=False, server_default=""),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("tipo IN ('backup', 'restauracao')", name="registro_operacao_tipo"),
    )
    op.create_index("ix_registro_operacao_tipo_feito_em", "registro_operacao", ["tipo", "feito_em"])
    op.execute("GRANT SELECT ON registro_operacao TO caderneta_app")


def downgrade() -> None:
    op.drop_table("registro_operacao")
