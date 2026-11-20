"""MO.4: avisos de operação (backup, teste de restauração, disco, memória) só para a direção."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import cli, operacao
from app.config import get_settings
from app.models import RegistroOperacao
from tests.conftest import Cliente


@pytest.fixture
def monitorado(monkeypatch):
    monkeypatch.setattr(get_settings(), "backup_monitorado", True)
    monkeypatch.setattr(get_settings(), "disco_max_pct", 101)  # a máquina do teste não interfere
    monkeypatch.setattr(get_settings(), "memoria_max_pct", 101)


def _registra(owner_engine, tipo: str, ha: timedelta) -> None:
    with Session(owner_engine) as db, db.begin():
        db.add(RegistroOperacao(tipo=tipo, feito_em=datetime.now(UTC) - ha, detalhe="x"))


def _codigos(c: Cliente) -> set[str]:
    r = c.get("/api/operacao")
    assert r.status_code == 200
    return {a["codigo"] for a in r.json()["avisos"]}


def test_so_a_direcao_ve(mundo, entrar):
    assert Cliente().get("/api/operacao").status_code == 401
    for email in ("prof.a@teste.com", "mae.a@teste.com", "aluno.a@teste.com"):
        assert entrar(email).get("/api/operacao").status_code == 403
    assert entrar("admin.a@teste.com").get("/api/operacao").status_code == 200


def test_sem_backup_e_sem_restauracao_avisa(mundo, entrar, monitorado):
    assert _codigos(entrar("admin.a@teste.com")) == {"backup", "restauracao"}


def test_backup_recente_nao_avisa_e_atrasado_avisa(mundo, entrar, monitorado, owner_engine):
    _registra(owner_engine, "restauracao", timedelta(days=3))
    _registra(owner_engine, "backup", timedelta(hours=30))
    c = entrar("admin.a@teste.com")
    assert _codigos(c) == {"backup"}
    assert "30 horas" in c.get("/api/operacao").json()["avisos"][0]["texto"]
    _registra(owner_engine, "backup", timedelta(hours=2))
    assert _codigos(c) == set()


def test_restauracao_vencida_avisa(mundo, entrar, monitorado, owner_engine):
    _registra(owner_engine, "backup", timedelta(hours=1))
    _registra(owner_engine, "restauracao", timedelta(days=45))
    assert _codigos(entrar("admin.a@teste.com")) == {"restauracao"}


def test_sem_monitoramento_nao_cobra_backup(mundo, entrar, monkeypatch):
    monkeypatch.setattr(get_settings(), "backup_monitorado", False)
    monkeypatch.setattr(get_settings(), "disco_max_pct", 101)
    monkeypatch.setattr(get_settings(), "memoria_max_pct", 101)
    d = entrar("admin.a@teste.com").get("/api/operacao").json()
    assert d["avisos"] == [] and d["backup_monitorado"] is False


def test_monitorado_por_padrao_so_em_producao(monkeypatch):
    monkeypatch.setattr(get_settings(), "backup_monitorado", None)
    monkeypatch.setattr(get_settings(), "env", "prod")
    assert operacao.backup_monitorado() is True
    monkeypatch.setattr(get_settings(), "env", "dev")
    assert operacao.backup_monitorado() is False


def test_disco_e_memoria_no_limite(mundo, entrar, monitorado, monkeypatch, owner_engine):
    _registra(owner_engine, "backup", timedelta(hours=1))
    _registra(owner_engine, "restauracao", timedelta(days=1))
    monkeypatch.setattr(operacao, "disco_pct", lambda _: 91)
    monkeypatch.setattr(operacao, "memoria_pct", lambda: 95)
    monkeypatch.setattr(get_settings(), "disco_max_pct", 85)
    monkeypatch.setattr(get_settings(), "memoria_max_pct", 90)
    d = entrar("admin.a@teste.com").get("/api/operacao").json()
    assert {a["codigo"] for a in d["avisos"]} == {"disco", "memoria"}
    assert d["disco_pct"] == 91 and d["memoria_pct"] == 95


def test_memoria_le_o_meminfo(tmp_path):
    m = tmp_path / "meminfo"
    m.write_text("MemTotal:       1000 kB\nMemFree:  100 kB\nMemAvailable:    250 kB\n")
    assert operacao.memoria_pct(m) == 75
    assert operacao.memoria_pct(tmp_path / "nao-existe") is None


def test_cli_registra_backup_e_restauracao(owner_engine, capsys):
    cli.registrar_backup("caderneta-20261120T030000Z.tar.gpg", 12345)
    cli.registrar_backup("ok", None, restauracao=True)
    with owner_engine.connect() as c:
        linhas = c.execute(text("SELECT tipo, detalhe, tamanho_bytes FROM registro_operacao ORDER BY id")).all()
    assert [tuple(x) for x in linhas] == [
        ("backup", "caderneta-20261120T030000Z.tar.gpg", 12345),
        ("restauracao", "ok", None),
    ]
    assert "registrado" in capsys.readouterr().out


def test_app_so_le_o_registro(owner_engine):
    """O papel do app não grava registros de operação: só o CLI (dono do banco) grava."""
    app_engine = create_engine(get_settings().database_url)
    try:
        with pytest.raises(Exception, match="permission denied"), app_engine.begin() as c:
            c.execute(text("INSERT INTO registro_operacao (tipo, detalhe) VALUES ('backup', 'falso')"))
    finally:
        app_engine.dispose()
