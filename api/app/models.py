"""Modelo de dados do M1. Toda tabela escolar tem `escola_id` e política RLS (ver migração 0001).

Valores padrão são gerados no Python (não no banco) para que os INSERTs não dependam de RETURNING,
que exigiria visibilidade pela política de leitura.
"""

import enum
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Time,
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
    # Provas e impressão (M5)
    aprovacao_impressao: Mapped[bool] = mapped_column(Boolean, default=True)
    reserva_copias: Mapped[int] = mapped_column(Integer, default=2)
    antecedencia_dias: Mapped[int] = mapped_column(Integer, default=2)
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
    # Notificações: e-mail ligado por padrão (só com texto mínimo), horário silencioso das 21h às 7h.
    notif_email: Mapped[bool] = mapped_column(Boolean, default=True)
    silencio_inicio: Mapped[time] = mapped_column(Time, default=time(21, 0))
    silencio_fim: Mapped[time] = mapped_column(Time, default=time(7, 0))
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


# --- M2: notas, médias e frequência ---------------------------------------------------------------------


class TipoMedia(enum.StrEnum):
    aritmetica = "aritmetica"
    ponderada = "ponderada"


class Recuperacao(enum.StrEnum):
    nenhuma = "nenhuma"
    substitui_se_maior = "substitui_se_maior"
    media = "media"


class Arredondamento(enum.StrEnum):
    nenhum = "nenhum"
    decimo = "decimo"
    meio = "meio"


class StatusNota(enum.StrEnum):
    normal = "normal"
    dispensada = "dispensada"
    falta_justificada = "falta_justificada"


class StatusPresenca(enum.StrEnum):
    presente = "presente"
    falta = "falta"
    justificada = "justificada"
    atraso = "atraso"


class RegraMedia(Base):
    """Regra de cálculo da escola num ano letivo. A média nunca é digitada: sai daqui."""

    __tablename__ = "regra_media"
    ano_letivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ano_letivo.id", ondelete="CASCADE"), primary_key=True)
    escola_id: Mapped[uuid.UUID] = _escola()
    tipo_media: Mapped[TipoMedia] = mapped_column(_enum(TipoMedia, "tipo_media"), default=TipoMedia.ponderada)
    pesos_periodos: Mapped[list | None] = mapped_column(JSONB)  # ex.: [2, 2, 3, 3]; None = todos iguais
    recuperacao: Mapped[Recuperacao] = mapped_column(
        _enum(Recuperacao, "recuperacao"), default=Recuperacao.substitui_se_maior
    )
    arredondamento: Mapped[Arredondamento] = mapped_column(
        _enum(Arredondamento, "arredondamento"), default=Arredondamento.decimo
    )
    nota_maxima: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal(10))
    media_aprovacao: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal(6))
    frequencia_minima: Mapped[int] = mapped_column(Integer, default=75)


class Avaliacao(Base):
    __tablename__ = "avaliacao"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    atribuicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("atribuicao.id", ondelete="CASCADE"), index=True)
    periodo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("periodo.id", ondelete="RESTRICT"), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(20), default="prova")  # prova, trabalho, participacao, simulado
    data: Mapped[date | None] = mapped_column(Date)
    peso: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal(1))
    nota_maxima: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal(10))
    recuperacao: Mapped[bool] = mapped_column(Boolean, default=False)
    publicada: Mapped[bool] = mapped_column(Boolean, default=False)
    notificada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Nota(Base):
    __tablename__ = "nota"
    __table_args__ = (UniqueConstraint("avaliacao_id", "matricula_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    avaliacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("avaliacao.id", ondelete="CASCADE"), index=True)
    matricula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matricula.id", ondelete="CASCADE"), index=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    status: Mapped[StatusNota] = mapped_column(_enum(StatusNota, "status_nota"), default=StatusNota.normal)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Aula(Base):
    __tablename__ = "aula"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    atribuicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("atribuicao.id", ondelete="CASCADE"), index=True)
    data: Mapped[date] = mapped_column(Date)
    quantidade: Mapped[int] = mapped_column(Integer, default=1)  # aula dupla = 2
    conteudo: Mapped[str | None] = mapped_column(String(300))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Frequencia(Base):
    """Só ausências, atrasos e justificativas são gravados; sem linha = presente."""

    __tablename__ = "frequencia"
    __table_args__ = (UniqueConstraint("aula_id", "matricula_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aula.id", ondelete="CASCADE"), index=True)
    matricula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matricula.id", ondelete="CASCADE"), index=True)
    status: Mapped[StatusPresenca] = mapped_column(_enum(StatusPresenca, "status_presenca"))
    justificativa: Mapped[str | None] = mapped_column(String(300))


# --- M3: comunicação ---------------------------------------------------------------------------------------


class EscopoAviso(enum.StrEnum):
    escola = "escola"
    turma = "turma"


class Aviso(Base):
    """Comunicado da escola (toda a escola) ou de uma turma. Só aparece a partir de `publicar_em`."""

    __tablename__ = "aviso"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    escopo: Mapped[EscopoAviso] = mapped_column(_enum(EscopoAviso, "escopo_aviso"))
    turma_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    corpo: Mapped[str] = mapped_column(String(10000))
    exige_ciente: Mapped[bool] = mapped_column(Boolean, default=False)
    publicar_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
    arquivado: Mapped[bool] = mapped_column(Boolean, default=False)
    notificado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_lembrete_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    autor: Mapped[Usuario | None] = relationship(lazy="joined")


class AvisoLeitura(Base):
    """Leitura e "ciente" de um aviso por um usuário (responsável ou aluno)."""

    __tablename__ = "aviso_leitura"
    __table_args__ = (UniqueConstraint("aviso_id", "usuario_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aviso_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aviso.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    lido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    ciente_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Autorizacao(Base):
    """Pedido de autorização às famílias (passeio, saída antecipada). Uma resposta por aluno."""

    __tablename__ = "autorizacao"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    turma_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str] = mapped_column(String(5000))
    data_evento: Mapped[date | None] = mapped_column(Date)
    prazo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arquivado: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    autor: Mapped[Usuario | None] = relationship(lazy="joined")


class AutorizacaoResposta(Base):
    """Resposta do responsável por um aluno; pode ser alterada até o prazo (cada troca é auditada)."""

    __tablename__ = "autorizacao_resposta"
    __table_args__ = (UniqueConstraint("autorizacao_id", "aluno_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    autorizacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("autorizacao.id", ondelete="CASCADE"), index=True)
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    autoriza: Mapped[bool] = mapped_column(Boolean)
    observacao: Mapped[str | None] = mapped_column(String(300))
    respondido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Conversa(Base):
    """Conversa sobre um aluno entre alguém da escola (`escola_usuario_id`) e os responsáveis dele."""

    __tablename__ = "conversa"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    escola_usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    assunto: Mapped[str] = mapped_column(String(200))
    ultima_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
    ultima_autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    ultima_previa: Mapped[str] = mapped_column(String(140), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    aluno: Mapped[Aluno] = relationship(lazy="joined")
    escola_usuario: Mapped[Usuario] = relationship(lazy="joined", foreign_keys=[escola_usuario_id])


class Mensagem(Base):
    __tablename__ = "mensagem"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    conversa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversa.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    corpo: Mapped[str] = mapped_column(String(5000))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    autor: Mapped[Usuario | None] = relationship(lazy="joined")


class MensagemAnexo(Base):
    """Anexo de uma mensagem (PDF ou imagem sem metadados). Some junto com o arquivo na retenção."""

    __tablename__ = "mensagem_anexo"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    mensagem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mensagem.id", ondelete="CASCADE"), index=True)
    arquivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("arquivo.id", ondelete="CASCADE"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)

    arquivo: Mapped["Arquivo"] = relationship(lazy="joined")


class ConversaLeitura(Base):
    """Até quando cada usuário leu a conversa (base do contador de não lidas)."""

    __tablename__ = "conversa_leitura"
    __table_args__ = (UniqueConstraint("conversa_id", "usuario_id"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    conversa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversa.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    lido_ate: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Notificacao(Base):
    """Notificação no app. O e-mail correspondente leva só um aviso genérico, nunca este texto."""

    __tablename__ = "notificacao"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    titulo: Mapped[str] = mapped_column(String(200))
    corpo: Mapped[str] = mapped_column(String(300), default="")
    url: Mapped[str] = mapped_column(String(200), default="/notificacoes")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_pendente: Mapped[bool] = mapped_column(Boolean, default=False)
    enviar_apos: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertaFalta(Base):
    """Marca que o alerta de 15% ou 20% de faltas já foi disparado para a matrícula (evita repetir)."""

    __tablename__ = "alerta_falta"
    __table_args__ = (UniqueConstraint("matricula_id", "nivel"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    matricula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matricula.id", ondelete="CASCADE"), index=True)
    nivel: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


# --- M4: calendário -------------------------------------------------------------------------------------


class TipoEvento(enum.StrEnum):
    feriado = "feriado"
    sem_aula = "sem_aula"
    avaliacao = "avaliacao"
    evento = "evento"
    prazo = "prazo"


BLOQUEIA_AULA = {TipoEvento.feriado, TipoEvento.sem_aula}


class Evento(Base):
    """Evento de dia inteiro. Sem `turma_id` vale para a escola toda; feriado e sem_aula bloqueiam a chamada."""

    __tablename__ = "evento"
    __table_args__ = (CheckConstraint("fim >= inicio", name="ck_evento_periodo"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    turma_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[TipoEvento] = mapped_column(_enum(TipoEvento, "tipo_evento"))
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str | None] = mapped_column(String(1000))
    inicio: Mapped[date] = mapped_column(Date, index=True)
    fim: Mapped[date] = mapped_column(Date)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    autor: Mapped[Usuario | None] = relationship(lazy="joined")


class CalendarioToken(Base):
    """Credencial da assinatura iCal de um perfil. Só o hash fica guardado; o link aparece uma vez."""

    __tablename__ = "calendario_token"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    perfil_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario_perfil.id", ondelete="CASCADE"), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


# --- M5: provas, trabalhos e impressão ----------------------------------------------------------------------


class TipoPedido(enum.StrEnum):
    prova = "prova"
    trabalho = "trabalho"
    lista = "lista"


class StatusPedido(enum.StrEnum):
    rascunho = "rascunho"
    enviada = "enviada"
    ajustes = "ajustes"
    aprovada = "aprovada"
    impressa = "impressa"


class Arquivo(Base):
    """Metadados de um arquivo. O conteúdo fica cifrado no armazenamento (ver `arquivos.py`)."""

    __tablename__ = "arquivo"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    nome: Mapped[str] = mapped_column(String(200))
    mime: Mapped[str] = mapped_column(String(100))
    tamanho: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    criado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class PedidoImpressao(Base):
    __tablename__ = "pedido_impressao"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"), index=True)
    atribuicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("atribuicao.id", ondelete="CASCADE"), index=True)
    arquivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("arquivo.id", ondelete="RESTRICT"))
    arquivo_adaptado_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("arquivo.id", ondelete="SET NULL"))
    tipo: Mapped[TipoPedido] = mapped_column(_enum(TipoPedido, "tipo_pedido"))
    titulo: Mapped[str] = mapped_column(String(200))
    data_aplicacao: Mapped[date] = mapped_column(Date, index=True)
    copias: Mapped[int] = mapped_column(Integer)
    copias_calculadas: Mapped[int] = mapped_column(Integer)
    copias_adaptadas: Mapped[int] = mapped_column(Integer, default=0)
    frente_verso: Mapped[bool] = mapped_column(Boolean, default=True)
    colorido: Mapped[bool] = mapped_column(Boolean, default=False)
    grampear: Mapped[bool] = mapped_column(Boolean, default=False)
    observacoes: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[StatusPedido] = mapped_column(_enum(StatusPedido, "status_pedido"), default=StatusPedido.rascunho)
    publicado: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aprovado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    impresso_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    impresso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    atribuicao: Mapped[Atribuicao] = relationship(lazy="joined")
    arquivo: Mapped[Arquivo] = relationship(lazy="joined", foreign_keys=[arquivo_id])
    arquivo_adaptado: Mapped[Arquivo | None] = relationship(lazy="joined", foreign_keys=[arquivo_adaptado_id])


class PedidoComentario(Base):
    __tablename__ = "pedido_comentario"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    pedido_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pedido_impressao.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    corpo: Mapped[str] = mapped_column(String(1000))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    autor: Mapped[Usuario | None] = relationship(lazy="joined")


# --- M6.2: anotações sobre o aluno --------------------------------------------------------------------------


class TipoAnotacao(enum.StrEnum):
    pedagogica = "pedagogica"
    ocorrencia = "ocorrencia"
    elogio = "elogio"
    reservada = "reservada"


class Anotacao(Base):
    """Registro sobre o aluno. Cada edição gera uma versão nova; a versão atual fica nesta linha."""

    __tablename__ = "anotacao"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    ano_letivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ano_letivo.id", ondelete="RESTRICT"))
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"), index=True)
    tipo: Mapped[TipoAnotacao] = mapped_column(_enum(TipoAnotacao, "tipo_anotacao"))
    visivel_responsaveis: Mapped[bool] = mapped_column(Boolean, default=False)
    corpo: Mapped[str] = mapped_column(String(5000))
    versao: Mapped[int] = mapped_column(Integer, default=1)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    removida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    removida_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))

    autor: Mapped[Usuario | None] = relationship(lazy="joined", foreign_keys=[autor_id])
    ano_letivo: Mapped[AnoLetivo] = relationship(lazy="joined")


class AnotacaoVersao(Base):
    __tablename__ = "anotacao_versao"
    __table_args__ = (UniqueConstraint("anotacao_id", "versao"),)
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    anotacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anotacao.id", ondelete="CASCADE"), index=True)
    versao: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[TipoAnotacao] = mapped_column(_enum(TipoAnotacao, "tipo_anotacao"))
    visivel_responsaveis: Mapped[bool] = mapped_column(Boolean, default=False)
    corpo: Mapped[str] = mapped_column(String(5000))
    editado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    editor: Mapped[Usuario | None] = relationship(lazy="joined")


class HistoricoEmitido(Base):
    """Registro de cada histórico escolar emitido (quem, quando) e o código impresso no PDF para conferência."""

    __tablename__ = "historico_emitido"
    id: Mapped[uuid.UUID] = _id()
    escola_id: Mapped[uuid.UUID] = _escola()
    aluno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    emitido_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    emitido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    codigo: Mapped[str] = mapped_column(String(16), unique=True)
    resumo_sha256: Mapped[str] = mapped_column(String(64))

    emissor: Mapped[Usuario | None] = relationship(lazy="joined")
