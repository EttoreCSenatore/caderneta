"""push: inscricoes de aparelhos e controle de envio

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notificacao", sa.Column("push_pendente", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("notificacao", sa.Column("push_enviado_em", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "push_inscricao",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("endpoint", sa.String(length=1000), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_uso_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )
    op.create_index(op.f("ix_push_inscricao_usuario_id"), "push_inscricao", ["usuario_id"])
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON push_inscricao TO caderneta_app")
    op.execute("ALTER TABLE push_inscricao ENABLE ROW LEVEL SECURITY")
    # cada pessoa só enxerga os próprios aparelhos; o worker (papel dono) envia para todos
    op.execute(
        "CREATE POLICY propria ON push_inscricao USING (usuario_id = app_usuario()) WITH CHECK (usuario_id = app_usuario())"
    )
    # Quando outra pessoa entra no mesmo navegador, o endereço do aparelho já existe com o dono antigo (que o RLS esconde).
    # Esta função apaga essa inscrição para o novo dono poder registrar o aparelho. O endereço é um segredo do aparelho.
    op.execute(
        """
        CREATE FUNCTION push_liberar_endpoint(p_endpoint text) RETURNS void
        LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
          DELETE FROM push_inscricao WHERE endpoint = p_endpoint
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION push_liberar_endpoint(text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION push_liberar_endpoint(text) TO caderneta_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS push_liberar_endpoint(text)")
    op.drop_table("push_inscricao")
    op.drop_column("notificacao", "push_enviado_em")
    op.drop_column("notificacao", "push_pendente")
