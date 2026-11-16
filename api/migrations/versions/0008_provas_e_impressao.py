"""provas, trabalhos e fila de impressao

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

NOVAS = ["arquivo", "pedido_impressao", "pedido_comentario"]


def upgrade() -> None:
    op.add_column("escola", sa.Column("aprovacao_impressao", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("escola", sa.Column("reserva_copias", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("escola", sa.Column("antecedencia_dias", sa.Integer(), nullable=False, server_default="2"))
    op.create_table(
        "arquivo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=False),
        sa.Column("tamanho", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("criado_por", sa.Uuid(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["criado_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_arquivo_escola_id"), "arquivo", ["escola_id"])
    op.create_table(
        "pedido_impressao",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("atribuicao_id", sa.Uuid(), nullable=False),
        sa.Column("arquivo_id", sa.Uuid(), nullable=False),
        sa.Column("arquivo_adaptado_id", sa.Uuid(), nullable=True),
        sa.Column("tipo", sa.Enum("prova", "trabalho", "lista", name="tipo_pedido"), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("data_aplicacao", sa.Date(), nullable=False),
        sa.Column("copias", sa.Integer(), nullable=False),
        sa.Column("copias_calculadas", sa.Integer(), nullable=False),
        sa.Column("copias_adaptadas", sa.Integer(), nullable=False),
        sa.Column("frente_verso", sa.Boolean(), nullable=False),
        sa.Column("colorido", sa.Boolean(), nullable=False),
        sa.Column("grampear", sa.Boolean(), nullable=False),
        sa.Column("observacoes", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("rascunho", "enviada", "ajustes", "aprovada", "impressa", name="status_pedido"),
            nullable=False,
        ),
        sa.Column("publicado", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enviado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aprovado_por", sa.Uuid(), nullable=True),
        sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("impresso_por", sa.Uuid(), nullable=True),
        sa.Column("impresso_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["aprovado_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["arquivo_adaptado_id"], ["arquivo.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["arquivo_id"], ["arquivo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["atribuicao_id"], ["atribuicao.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["impresso_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ("escola_id", "autor_id", "atribuicao_id", "data_aplicacao"):
        op.create_index(op.f(f"ix_pedido_impressao_{c}"), "pedido_impressao", [c])
    op.create_table(
        "pedido_comentario",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("pedido_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("corpo", sa.String(length=1000), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido_impressao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pedido_comentario_escola_id"), "pedido_comentario", ["escola_id"])
    op.create_index(op.f("ix_pedido_comentario_pedido_id"), "pedido_comentario", ["pedido_id"])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("pedido_comentario")
    op.drop_table("pedido_impressao")
    op.drop_table("arquivo")
    op.drop_column("escola", "antecedencia_dias")
    op.drop_column("escola", "reserva_copias")
    op.drop_column("escola", "aprovacao_impressao")
    op.execute("DROP TYPE IF EXISTS tipo_pedido")
    op.execute("DROP TYPE IF EXISTS status_pedido")
