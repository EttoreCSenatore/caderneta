"""pedidos de titulares de dados (LGPD art. 18): protocolo, prazo e resposta

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pedido_titular",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("solicitante_id", sa.Uuid(), nullable=True),
        sa.Column("aluno_id", sa.Uuid(), nullable=True),
        sa.Column("titular_nome", sa.String(200), nullable=True),
        sa.Column("titular_contato", sa.String(200), nullable=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("canal", sa.String(20), nullable=False, server_default="app"),
        sa.Column("descricao", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="aberto"),
        sa.Column("recebido_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prazo_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resposta", sa.String(4000), nullable=True),
        sa.Column("respondido_por", sa.Uuid(), nullable=True),
        sa.Column("respondido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["solicitante_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["aluno_id"], ["aluno.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["respondido_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pedido_titular_escola_id", "pedido_titular", ["escola_id"])
    op.create_index("ix_pedido_titular_solicitante_id", "pedido_titular", ["solicitante_id"])
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON pedido_titular TO caderneta_app")
    op.execute("ALTER TABLE pedido_titular ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY isolamento ON pedido_titular USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
    )


def downgrade() -> None:
    op.drop_table("pedido_titular")
