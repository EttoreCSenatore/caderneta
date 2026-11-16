"""historico escolar emitido e verificacao publica

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "historico_emitido",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("aluno_id", sa.Uuid(), nullable=False),
        sa.Column("emitido_por", sa.Uuid(), nullable=True),
        sa.Column("emitido_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("codigo", sa.String(length=16), nullable=False),
        sa.Column("resumo_sha256", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["aluno_id"], ["aluno.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["emitido_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    op.create_index(op.f("ix_historico_emitido_escola_id"), "historico_emitido", ["escola_id"])
    op.create_index(op.f("ix_historico_emitido_aluno_id"), "historico_emitido", ["aluno_id"])
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON historico_emitido TO caderneta_app")
    op.execute("ALTER TABLE historico_emitido ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY isolamento ON historico_emitido "
        "USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
    )
    # Conferência pública do código impresso no PDF. É uma função com SECURITY DEFINER para poder ler sem escola ativa
    # (quem confere não tem login) e devolve o mínimo: a escola, a data e as iniciais do aluno. Nada de notas ou datas de nascimento.
    op.execute(
        """
        CREATE FUNCTION verificar_historico(p_codigo text)
        RETURNS TABLE (escola text, emitido_em timestamptz, iniciais text)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
          SELECT e.nome, h.emitido_em,
                 upper(left(a.nome, 1)) || '. ' || upper(left(a.sobrenome, 1)) || '.'
          FROM historico_emitido h
          JOIN escola e ON e.id = h.escola_id
          JOIN aluno a ON a.id = h.aluno_id
          WHERE h.codigo = upper(p_codigo)
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION verificar_historico(text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION verificar_historico(text) TO caderneta_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS verificar_historico(text)")
    op.drop_table("historico_emitido")
