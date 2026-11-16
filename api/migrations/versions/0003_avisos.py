"""avisos e leituras

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

NOVAS = ["aviso", "aviso_leitura"]


def upgrade() -> None:
    op.create_table(
        "aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("escopo", sa.Enum("escola", "turma", name="escopo_aviso"), nullable=False),
        sa.Column("turma_id", sa.Uuid(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("corpo", sa.String(length=10000), nullable=False),
        sa.Column("exige_ciente", sa.Boolean(), nullable=False),
        sa.Column("publicar_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arquivado", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turma_id"], ["turma.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aviso_escola_id"), "aviso", ["escola_id"])
    op.create_index(op.f("ix_aviso_turma_id"), "aviso", ["turma_id"])
    op.create_index(op.f("ix_aviso_publicar_em"), "aviso", ["publicar_em"])
    op.create_table(
        "aviso_leitura",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("aviso_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("lido_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ciente_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["aviso_id"], ["aviso.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aviso_id", "usuario_id"),
    )
    op.create_index(op.f("ix_aviso_leitura_escola_id"), "aviso_leitura", ["escola_id"])
    op.create_index(op.f("ix_aviso_leitura_aviso_id"), "aviso_leitura", ["aviso_id"])
    op.create_index(op.f("ix_aviso_leitura_usuario_id"), "aviso_leitura", ["usuario_id"])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("aviso_leitura")
    op.drop_table("aviso")
    op.execute("DROP TYPE IF EXISTS escopo_aviso")
