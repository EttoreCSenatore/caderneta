"""notificacoes, preferencias e alertas de faltas

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

NOVAS = ["notificacao", "alerta_falta"]


def upgrade() -> None:
    op.add_column("usuario", sa.Column("notif_email", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("usuario", sa.Column("silencio_inicio", sa.Time(), nullable=False, server_default="21:00"))
    op.add_column("usuario", sa.Column("silencio_fim", sa.Time(), nullable=False, server_default="07:00"))
    op.add_column("avaliacao", sa.Column("notificada_em", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE avaliacao SET notificada_em = now() WHERE publicada")
    op.add_column("aviso", sa.Column("notificado_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("aviso", sa.Column("ultimo_lembrete_em", sa.DateTime(timezone=True), nullable=True))
    # avisos já publicados antes desta migração não geram notificação retroativa
    op.execute("UPDATE aviso SET notificado_em = publicar_em WHERE publicar_em <= now()")
    op.create_table(
        "notificacao",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("corpo", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=200), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_pendente", sa.Boolean(), nullable=False),
        sa.Column("enviar_apos", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_enviado_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ("escola_id", "usuario_id", "criado_em"):
        op.create_index(op.f(f"ix_notificacao_{c}"), "notificacao", [c])
    op.create_table(
        "alerta_falta",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("escola_id", sa.Uuid(), nullable=False),
        sa.Column("matricula_id", sa.Uuid(), nullable=False),
        sa.Column("nivel", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["escola_id"], ["escola.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matricula_id"], ["matricula.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matricula_id", "nivel"),
    )
    op.create_index(op.f("ix_alerta_falta_escola_id"), "alerta_falta", ["escola_id"])
    op.create_index(op.f("ix_alerta_falta_matricula_id"), "alerta_falta", ["matricula_id"])
    for t in NOVAS:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO caderneta_app")
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY isolamento ON {t} USING (escola_id = app_escola()) WITH CHECK (escola_id = app_escola())"
        )


def downgrade() -> None:
    op.drop_table("alerta_falta")
    op.drop_table("notificacao")
    op.drop_column("avaliacao", "notificada_em")
    op.drop_column("aviso", "ultimo_lembrete_em")
    op.drop_column("aviso", "notificado_em")
    op.drop_column("usuario", "silencio_fim")
    op.drop_column("usuario", "silencio_inicio")
    op.drop_column("usuario", "notif_email")
