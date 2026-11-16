"""anotacoes versionadas

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

NOVAS = ["anotacao", "anotacao_versao"]
TIPO = postgresql.ENUM("pedagogica", "ocorrencia", "elogio", "reservada", name="tipo_anotacao", create_type=False)


def upgrade() -> None:
    op.execute("CREATE TYPE tipo_anotacao AS ENUM ('pedagogica', 'ocorrencia', 'elogio', 'reservada')")
    op.create_table(
        "anotacao",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("aluno_id", sa.Uuid(), nullable=False),
        sa.Column("ano_letivo_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("tipo", TIPO, nullable=False),
        sa.Column("visivel_responsaveis", sa.Boolean(), nullable=False),
        sa.Column("corpo", sa.String(length=5000), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removida_por", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["aluno_id"], ["aluno.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ano_letivo_id"], ["ano_letivo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["removida_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ("escola_id", "aluno_id", "autor_id", "removida_em"):
        op.create_index(op.f(f"ix_anotacao_{c}"), "anotacao", [c])
    op.create_table(
        "anotacao_versao",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("anotacao_id", sa.Uuid(), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("tipo", TIPO, nullable=False),
        sa.Column("visivel_responsaveis", sa.Boolean(), nullable=False),
        sa.Column("corpo", sa.String(length=5000), nullable=False),
        sa.Column("editado_por", sa.Uuid(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["anotacao_id"], ["anotacao.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["editado_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("anotacao_id", "versao"),
    )
    op.create_index(op.f("ix_anotacao_versao_escola_id"), "anotacao_versao", ["escola_id"])
    op.create_index(op.f("ix_anotacao_versao_anotacao_id"), "anotacao_versao", ["anotacao_id"])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("anotacao_versao")
    op.drop_table("anotacao")
    op.execute("DROP TYPE IF EXISTS tipo_anotacao")
