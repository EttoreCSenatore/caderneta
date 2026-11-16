"""desligados: datas de desligamento, prazos de retencao e adiamentos

Revision ID: 0013
Revises: 0012
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("escola", sa.Column("retencao_aluno_desligado_dias", sa.Integer(), nullable=False, server_default="365"))
    op.add_column("escola", sa.Column("retencao_usuario_desligado_dias", sa.Integer(), nullable=False, server_default="180"))
    op.add_column("escola", sa.Column("aviso_desligados_dias", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("usuario", sa.Column("anonimizado_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuario_perfil", sa.Column("desligado_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuario_perfil", sa.Column("anonimizacao_adiada_ate", sa.Date(), nullable=True))
    op.add_column("usuario_perfil", sa.Column("anonimizacao_avisada_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("aluno", sa.Column("desligado_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("aluno", sa.Column("purga_adiada_ate", sa.Date(), nullable=True))
    op.add_column("aluno", sa.Column("purga_avisada_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("aluno", sa.Column("purgado_em", sa.DateTime(timezone=True), nullable=True))
    # Quem já estava desligado começa a contagem agora (nada é apagado retroativamente).
    op.execute("UPDATE aluno SET desligado_em = now() WHERE situacao <> 'ativo'")
    op.execute("UPDATE usuario_perfil SET desligado_em = now() WHERE NOT ativo")


def downgrade() -> None:
    for t, cols in (
        ("aluno", ("purgado_em", "purga_avisada_em", "purga_adiada_ate", "desligado_em")),
        ("usuario_perfil", ("anonimizacao_avisada_em", "anonimizacao_adiada_ate", "desligado_em")),
        ("usuario", ("anonimizado_em",)),
        ("escola", ("aviso_desligados_dias", "retencao_usuario_desligado_dias", "retencao_aluno_desligado_dias")),
    ):
        for c in cols:
            op.drop_column(t, c)
