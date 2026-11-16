"""conversas e mensagens

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

NOVAS = ["conversa", "mensagem", "conversa_leitura"]


def upgrade() -> None:
    op.create_table(
        "conversa",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("aluno_id", sa.Uuid(), nullable=False),
        sa.Column("escola_usuario_id", sa.Uuid(), nullable=False),
        sa.Column("assunto", sa.String(length=200), nullable=False),
        sa.Column("ultima_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultima_autor_id", sa.Uuid(), nullable=True),
        sa.Column("ultima_previa", sa.String(length=140), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["aluno_id"], ["aluno.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ultima_autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ("escola_id", "aluno_id", "escola_usuario_id", "ultima_em"):
        op.create_index(op.f(f"ix_conversa_{c}"), "conversa", [c])
    op.create_table(
        "mensagem",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("conversa_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("corpo", sa.String(length=5000), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversa.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mensagem_escola_id"), "mensagem", ["escola_id"])
    op.create_index(op.f("ix_mensagem_conversa_id"), "mensagem", ["conversa_id"])
    op.create_table(
        "conversa_leitura",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("conversa_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("lido_ate", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversa.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversa_id", "usuario_id"),
    )
    for c in ("escola_id", "conversa_id", "usuario_id"):
        op.create_index(op.f(f"ix_conversa_leitura_{c}"), "conversa_leitura", [c])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("conversa_leitura")
    op.drop_table("mensagem")
    op.drop_table("conversa")
