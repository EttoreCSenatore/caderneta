"""Modelo de dados do M1. Toda tabela escolar tem `escola_id` e política RLS (ver migração 0001).

Valores padrão são gerados no Python (não no banco) para que os INSERTs não dependam de RETURNING,
que exigiria visibilidade pela política de leitura.
"""

import enum
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def agora() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Papel(enum.StrEnum):
    admin = "admin"
    coordenacao = "coordenacao"
    professor = "professor"
    responsavel = "responsavel"
    aluno = "aluno"


STAFF = {Papel.admin, Papel.coordenacao}


class TipoPeriodo(enum.StrEnum):
    bimestre = "bimestre"
    trimestre = "trimestre"
    semestre = "semestre"


class SituacaoAluno(enum.StrEnum):
    ativo = "ativo"
    transferido = "transferido"
    concluiu = "concluiu"
    arquivado = "arquivado"


def _enum(e: type[enum.Enum], name: str) -> Enum:
    return Enum(e, name=name, values_callable=lambda x: [m.value for m in x])


def _id() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _escola() -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey("escola.id", ondelete="CASCADE"), index=True)


class Escola(Base):
    __tablename__ = "escola"
    id: Mapped[uuid.UUID] = _id()
    nome: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str | None] = mapped_column(String(18))
    cidade: Mapped[str | None] = mapped_column(String(120))
    uf: Mapped[str | None] = mapped_column(String(2))
    fuso: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Usuario(Base):
    __tablename__ = "usuario"
    id: Mapped[uuid.UUID] = _id()
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    nome: Mapped[str] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(30))
    senha_hash: Mapped[str | None] = mapped_column(String(255))
    totp_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    totp_ativo: Mapped[bool] = mapped_column(Boolean, default=False)
    falhas_login: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class UsuarioPerfil(Base):
    __tablename__ = "usuario_perfil"
    __table_args__ = (UniqueConstraint("usuario_id", "escola_id", "papel"),)
    id: Mapped[uuid.UUID] = _id()
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    escola_id: Mapped[uuid.UUID] = _escola()
    papel: Mapped[Papel] = mapped_column(_enum(Papel, "papel"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    usuario: Mapped[Usuario] = relationship(lazy="joined")


class Sessao(Base):
    """Sessões do servidor. Só o hash do token é guardado."""

    __tablename__ = "sessao"
    id: Mapped[uuid.UUID] = _id()
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    perfil_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario_perfil.id", ondelete="SET NULL"))
    mfa_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    ultimo_uso: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(300))


class TokenSenha(Base):
    __tablename__ = "token_senha"
    id: Mapped[uuid.UUID] = _id()
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnoLetivo(Base):
    __tablename__ = "ano_letivo"
    __table_args__ = (UniqueConstraint("escola_id", "ano"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    ano: Mapped[int] = mapped_column(Integer)
    tipo_periodo: Mapped[TipoPeriodo] = mapped_column(_enum(TipoPeriodo, "tipo_periodo"))
    inicio: Mapped[date] = mapped_column(Date)
    fim: Mapped[date] = mapped_column(Date)
    aberto: Mapped[bool] = mapped_column(Boolean, default=True)

    periodos: Mapped[list["Periodo"]] = relationship(order_by="Periodo.numero", lazy="selectin")


class Periodo(Base):
    __tablename__ = "periodo"
    __table_args__ = (UniqueConstraint("ano_letivo_id", "numero"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    ano_letivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ano_letivo.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(Integer)
    nome: Mapped[str] = mapped_column(String(40))
    inicio: Mapped[date] = mapped_column(Date)
    fim: Mapped[date] = mapped_column(Date)
    fechado: Mapped[bool] = mapped_column(Boolean, default=False)


class Disciplina(Base):
    __tablename__ = "disciplina"
    __table_args__ = (UniqueConstraint("escola_id", "nome"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    nome: Mapped[str] = mapped_column(String(80))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Turma(Base):
    __tablename__ = "turma"
    __table_args__ = (UniqueConstraint("ano_letivo_id", "nome"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    ano_letivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ano_letivo.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(40))
    serie: Mapped[str] = mapped_column(String(40))
    turno: Mapped[str] = mapped_column(String(20), default="manhã")


class Atribuicao(Base):
    """Professor × turma × disciplina: define o que cada professor acessa."""

    __tablename__ = "atribuicao"
    __table_args__ = (UniqueConstraint("turma_id", "disciplina_id", "professor_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    turma_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), index=True)
    disciplina_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("disciplina.id", ondelete="CASCADE"))
    professor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)

    disciplina: Mapped[Disciplina] = relationship(lazy="joined")
    professor: Mapped[Usuario] = relationship(lazy="joined")


class Aluno(Base):
    __tablename__ = "aluno"
    __table_args__ = (UniqueConstraint("escola_id", "ra"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    nome: Mapped[str] = mapped_column(String(120))
    sobrenome: Mapped[str] = mapped_column(String(120))
    nome_social: Mapped[str | None] = mapped_column(String(120))
    data_nascimento: Mapped[date] = mapped_column(Date)
    ra: Mapped[str | None] = mapped_column(String(30))
    cpf: Mapped[str | None] = mapped_column(String(14))
    situacao: Mapped[SituacaoAluno] = mapped_column(_enum(SituacaoAluno, "situacao_aluno"), default="ativo")
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Matricula(Base):
    """Âncora do histórico: liga aluno a uma turma num ano letivo."""

    __tablename__ = "matricula"
    __table_args__ = (UniqueConstraint("aluno_id", "ano_letivo_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    turma_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("turma.id", ondelete="RESTRICT"), index=True)
    ano_letivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ano_letivo.id", ondelete="CASCADE"))
    situacao: Mapped[str] = mapped_column(String(20), default="cursando")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    turma: Mapped[Turma] = relationship(lazy="joined")


class VinculoResponsavel(Base):
    """Contato familiar do aluno. `usuario_id` é preenchido quando o convite é aceito."""

    __tablename__ = "vinculo_responsavel"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"), index=True)
    nome: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))  # mae, pai, tutor, avo, outro
    telefone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(CITEXT)
    pode_buscar: Mapped[bool] = mapped_column(Boolean, default=True)
    recebe_avisos: Mapped[bool] = mapped_column(Boolean, default=True)
    emergencia: Mapped[bool] = mapped_column(Boolean, default=False)
    restrito: Mapped[bool] = mapped_column(Boolean, default=False)


class FichaSaude(Base):
    """Dados sensíveis (LGPD art. 11): conteúdo criptografado com AES-GCM; leituras auditadas."""

    __tablename__ = "ficha_saude"
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), primary_key=True)
    escola_id: Mapped[uuid.UUID] = _escola()
    dados_enc: Mapped[bytes] = mapped_column(LargeBinary)
    alerta_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Convite(Base):
    __tablename__ = "convite"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    email: Mapped[str] = mapped_column(CITEXT)
    nome: Mapped[str] = mapped_column(String(200))
    papel: Mapped[Papel] = mapped_column(_enum(Papel, "papel"))
    vinculo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vinculo_responsavel.id", ondelete="CASCADE"))
    aluno_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    aceito_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revogado: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Auditoria(Base):
    """Só inserção: a API não tem permissão de UPDATE/DELETE nesta tabela."""

    __tablename__ = "auditoria"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("escola.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column()
    acao: Mapped[str] = mapped_column(String(60))
    entidade: Mapped[str | None] = mapped_column(String(40))
    entidade_id: Mapped[str | None] = mapped_column(String(64))
    detalhes: Mapped[dict | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(String(64))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
