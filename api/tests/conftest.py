"""Testes contra um PostgreSQL real (banco caderneta_test), usando o papel restrito da API.

Assim o Row-Level Security é exercitado de verdade, não simulado.
"""

import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import date

os.environ.setdefault(
    "CADERNETA_DATABASE_URL", "postgresql+psycopg://caderneta_app:dev-app@127.0.0.1:5433/caderneta_test"
)
os.environ.setdefault(
    "CADERNETA_OWNER_DATABASE_URL", "postgresql+psycopg://caderneta_owner:dev-owner@127.0.0.1:5433/caderneta_test"
)
os.environ["CADERNETA_MAIL_BACKEND"] = "memory"
os.environ["CADERNETA_STORAGE_DIR"] = tempfile.mkdtemp(prefix="caderneta-test-storage-")
os.environ["CADERNETA_ENV"] = "test"

import pyotp  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import mail  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Aluno,
    AnoLetivo,
    Atribuicao,
    Base,
    Disciplina,
    Escola,
    Matricula,
    Papel,
    Periodo,
    TipoPeriodo,
    Turma,
    Usuario,
    UsuarioPerfil,
    VinculoResponsavel,
)
from app.security import cifra, hash_senha  # noqa: E402

SENHA = "senha-de-teste-123"
_HASH = hash_senha(SENHA)
API = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def owner_engine():
    url = get_settings().owner_database_url
    eng = create_engine(url)
    with eng.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        c.execute(text("GRANT USAGE ON SCHEMA public TO caderneta_app; CREATE EXTENSION IF NOT EXISTS citext;"))
    cfg = Config(os.path.join(API, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(API, "migrations"))
    cfg.attributes["url"] = url
    command.upgrade(cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def limpa(owner_engine):
    tabelas = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with owner_engine.begin() as c:
        c.execute(text(f"TRUNCATE {tabelas} CASCADE"))
    mail.outbox.clear()
    yield


@dataclass
class Escolinha:
    escola: Escola
    ano: AnoLetivo
    turma: Turma
    turma2: Turma
    disciplina: Disciplina
    usuarios: dict[str, Usuario] = field(default_factory=dict)
    alunos: dict[str, Aluno] = field(default_factory=dict)
    vinculos: dict[str, VinculoResponsavel] = field(default_factory=dict)


def _usuario(db: Session, escola: Escola, email: str, papel: Papel, totp: str | None = None) -> Usuario:
    u = Usuario(id=uuid.uuid4(), email=email, nome=email.split("@")[0].title(), senha_hash=_HASH)
    if totp:
        u.totp_secret_enc = cifra(totp, str(u.id))
        u.totp_ativo = True
    db.add(u)
    db.flush()
    db.add(UsuarioPerfil(usuario_id=u.id, escola_id=escola.id, papel=papel))
    return u


TOTP = pyotp.random_base32()


def _escola(db: Session, sufixo: str) -> Escolinha:
    e = Escola(id=uuid.uuid4(), nome=f"Escola {sufixo}")
    db.add(e)
    db.flush()
    ano = AnoLetivo(
        escola_id=e.id, ano=2026, tipo_periodo=TipoPeriodo.bimestre, inicio=date(2026, 2, 2), fim=date(2026, 12, 11)
    )
    db.add(ano)
    db.flush()
    db.add(
        Periodo(
            escola_id=e.id,
            ano_letivo_id=ano.id,
            numero=1,
            nome="1º bimestre",
            inicio=date(2026, 2, 2),
            fim=date(2026, 4, 17),
        )
    )
    t1 = Turma(escola_id=e.id, ano_letivo_id=ano.id, nome="7º A", serie="7º ano")
    t2 = Turma(escola_id=e.id, ano_letivo_id=ano.id, nome="8º B", serie="8º ano")
    d = Disciplina(escola_id=e.id, nome="Matemática")
    db.add_all([t1, t2, d])
    db.flush()
    w = Escolinha(e, ano, t1, t2, d)
    s = sufixo.lower()
    w.usuarios["admin"] = _usuario(db, e, f"admin.{s}@teste.com", Papel.admin, totp=TOTP)
    w.usuarios["coord"] = _usuario(db, e, f"coord.{s}@teste.com", Papel.coordenacao, totp=TOTP)
    w.usuarios["prof"] = _usuario(db, e, f"prof.{s}@teste.com", Papel.professor)
    w.usuarios["prof2"] = _usuario(db, e, f"prof2.{s}@teste.com", Papel.professor)
    w.usuarios["mae"] = _usuario(db, e, f"mae.{s}@teste.com", Papel.responsavel)
    w.usuarios["aluno"] = _usuario(db, e, f"aluno.{s}@teste.com", Papel.aluno)
    db.add(Atribuicao(escola_id=e.id, turma_id=t1.id, disciplina_id=d.id, professor_id=w.usuarios["prof"].id))
    for chave, nome, turma, conta in (
        ("joao", "João", t1, "aluno"),
        ("maria", "Maria", t1, None),
        ("pedro", "Pedro", t2, None),
    ):
        a = Aluno(
            escola_id=e.id,
            nome=nome,
            sobrenome=f"Silva {sufixo}",
            data_nascimento=date(2013, 5, 1),
            ra=f"{s}-{chave}",
            usuario_id=w.usuarios[conta].id if conta else None,
        )
        db.add(a)
        db.flush()
        db.add(Matricula(escola_id=e.id, aluno_id=a.id, turma_id=turma.id, ano_letivo_id=ano.id))
        w.alunos[chave] = a
    v = VinculoResponsavel(
        escola_id=e.id,
        aluno_id=w.alunos["joao"].id,
        usuario_id=w.usuarios["mae"].id,
        nome="Mãe do João",
        tipo="mae",
        email=f"mae.{s}@teste.com",
        emergencia=True,
    )
    v_restrito = VinculoResponsavel(
        escola_id=e.id, aluno_id=w.alunos["joao"].id, nome="Pai (restrito)", tipo="pai", restrito=True
    )
    db.add_all([v, v_restrito])
    db.flush()
    w.vinculos["mae"], w.vinculos["pai"] = v, v_restrito
    return w


@pytest.fixture
def mundo(owner_engine) -> tuple[Escolinha, Escolinha]:
    with Session(owner_engine, expire_on_commit=False) as db, db.begin():
        a, b = _escola(db, "A"), _escola(db, "B")
    return a, b


class Cliente(TestClient):
    """TestClient que manda o cabeçalho anti-CSRF por padrão."""

    def __init__(self):
        super().__init__(app, headers={"X-Caderneta": "1"})


def entra(email: str, senha: str = SENHA, perfil_id: uuid.UUID | None = None) -> Cliente:
    c = Cliente()
    r = c.post("/api/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.text
    if r.json()["status"] == "codigo":
        r = c.post("/api/auth/codigo", json={"codigo": pyotp.TOTP(TOTP).now()})
        assert r.status_code == 200, r.text
    if perfil_id:
        assert c.post("/api/auth/perfil", json={"perfil_id": str(perfil_id)}).status_code == 200
    return c


@pytest.fixture
def entrar():
    return entra
