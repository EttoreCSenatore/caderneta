"""autorizacoes

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

NOVAS = ["autorizacao", "autorizacao_resposta"]


def upgrade() -> None:
    op.create_table(
        "autorizacao",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("turma_id", sa.Uuid(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descricao", sa.String(length=5000), nullable=False),
        sa.Column("data_evento", sa.Date(), nullable=True),
        sa.Column("prazo", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arquivado", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turma_id"], ["turma.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_autorizacao_escola_id"), "autorizacao", ["escola_id"])
    op.create_index(op.f("ix_autorizacao_turma_id"), "autorizacao", ["turma_id"])
    op.create_table(
        "autorizacao_resposta",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("autorizacao_id", sa.Uuid(), nullable=False),
        sa.Column("aluno_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("autoriza", sa.Boolean(), nullable=False),
        sa.Column("observacao", sa.String(length=300), nullable=True),
        sa.Column("respondido_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["aluno_id"], ["aluno.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autorizacao_id"], ["autorizacao.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("autorizacao_id", "aluno_id"),
    )
    op.create_index(op.f("ix_autorizacao_resposta_escola_id"), "autorizacao_resposta", ["escola_id"])
    op.create_index(op.f("ix_autorizacao_resposta_autorizacao_id"), "autorizacao_resposta", ["autorizacao_id"])
    op.create_index(op.f("ix_autorizacao_resposta_aluno_id"), "autorizacao_resposta", ["aluno_id"])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("autorizacao_resposta")
    op.drop_table("autorizacao")
