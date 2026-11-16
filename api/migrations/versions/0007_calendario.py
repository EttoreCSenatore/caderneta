"""calendario: eventos e assinatura ical

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

NOVAS = ["evento", "calendario_token"]


def upgrade() -> None:
    op.create_table(
        "evento",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("turma_id", sa.Uuid(), nullable=True),
        sa.Column(
            "tipo", sa.Enum("feriado", "sem_aula", "avaliacao", "evento", "prazo", name="tipo_evento"), nullable=False
        ),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descricao", sa.String(length=1000), nullable=True),
        sa.Column("inicio", sa.Date(), nullable=False),
        sa.Column("fim", sa.Date(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("fim >= inicio", name="ck_evento_periodo"),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turma_id"], ["turma.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ("escola_id", "turma_id", "inicio"):
        op.create_index(op.f(f"ix_evento_{c}"), "evento", [c])
    op.create_table(
        "calendario_token",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("perfil_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["perfil_id"], ["usuario_perfil.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("perfil_id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_calendario_token_escola_id"), "calendario_token", ["escola_id"])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("calendario_token")
    op.drop_table("evento")
    op.execute("DROP TYPE IF EXISTS tipo_evento")
