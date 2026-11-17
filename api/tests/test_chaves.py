"""M8.5: rotação da chave de dados e logs de acesso sem dado pessoal."""

import base64
import hashlib
import logging
import os

import pytest
from sqlalchemy.orm import Session

from app import security
from app.chaves import rotaciona
from app.config import get_settings
from app.logs import FiltroAcesso, limpa_caminho
from tests.conftest import entra
from tests.test_arquivos import PDF

CHAVE_DEV = base64.urlsafe_b64encode(hashlib.sha256(b"caderneta-dev-key").digest()).decode()
CHAVE_NOVA = base64.urlsafe_b64encode(os.urandom(32)).decode()


@pytest.fixture
def chaves():
    security._chaves.cache_clear()
    yield
    security._chaves.cache_clear()


def _usa(monkeypatch, atual="", antigas=""):
    monkeypatch.setattr(get_settings(), "data_key", atual)
    monkeypatch.setattr(get_settings(), "data_keys_antigas", antigas)
    security._chaves.cache_clear()


def test_rotacao_regrava_saude_2fa_e_arquivos_sem_perder_nada(mundo, entrar, owner_engine, monkeypatch, chaves):
    from app import arquivos

    a, _ = mundo
    joao = a.alunos["joao"]
    admin = entrar("admin.a@teste.com")
    assert (
        admin.put(f"/api/alunos/{joao.id}/saude", json={"alergias": "amendoim", "alerta": "Alergia grave"}).status_code
        == 200
    )
    with Session(owner_engine) as db, db.begin():
        arq = arquivos.grava(
            db, escola_id=a.escola.id, usuario_id=a.usuarios["prof"].id, nome="p.pdf", dados=PDF + b"rotacao"
        )
        arq_id = arq.id

    # troca de chave: a nova grava, a antiga (a de desenvolvimento, que cifrou tudo acima) só lê
    _usa(monkeypatch, CHAVE_NOVA, CHAVE_DEV)
    assert admin.get(f"/api/alunos/{joao.id}/saude").json()["alergias"] == "amendoim"  # ainda lê com a chave antiga
    assert entra("admin.a@teste.com")  # o 2FA também (segredo ainda na chave antiga)

    with Session(owner_engine) as db, db.begin():
        simulado = rotaciona(db, simular=True)
    assert (
        simulado["saude"] == 1
        and simulado["arquivos"] == 1
        and simulado["segredos_2fa"] >= 2
        and simulado["pendentes"] >= 4
    )
    with Session(owner_engine) as db, db.begin():
        feito = rotaciona(db)
    assert feito["saude"] == 1 and feito["arquivos"] == 1 and feito["pendentes"] == 0
    with Session(owner_engine) as db, db.begin():
        again = rotaciona(db)
    assert (again["saude"], again["segredos_2fa"], again["arquivos"]) == (0, 0, 0)  # idempotente

    # a chave antiga pode sair: tudo continua legível só com a nova
    _usa(monkeypatch, CHAVE_NOVA, "")
    assert admin.get(f"/api/alunos/{joao.id}/saude").json()["alerta"] == "Alergia grave"
    assert entra("admin.a@teste.com")
    with Session(owner_engine) as db:
        assert arquivos.le(db.get(arquivos.Arquivo, arq_id)).endswith(b"rotacao")


def test_sem_a_chave_antiga_o_dado_nao_abre(monkeypatch, chaves):
    dado = security.cifra("segredo", "ctx")  # chave de desenvolvimento
    _usa(monkeypatch, CHAVE_NOVA, "")  # trocou a chave sem rotacionar e sem guardar a antiga
    with pytest.raises(security.InvalidTag):
        security.decifra(dado, "ctx")
    _usa(monkeypatch, CHAVE_NOVA, CHAVE_DEV)  # com a antiga guardada, abre
    assert security.decifra(dado, "ctx") == "segredo"
    assert security.na_chave_atual(dado, "ctx") is False


def test_chave_com_tamanho_errado_e_recusada(monkeypatch, chaves):
    _usa(monkeypatch, base64.urlsafe_b64encode(b"curta").decode(), "")
    with pytest.raises(RuntimeError):
        security._chaves()


# --- logs ---------------------------------------------------------------------------------------------------


def test_log_de_acesso_tira_query_string_e_segredos():
    assert limpa_caminho("/api/alunos?busca=Maria+Souza&turma=1") == "/api/alunos"
    assert limpa_caminho("/api/convites/abrir/ABC-secreto_123") == "/api/convites/abrir/<token>"
    assert limpa_caminho("/api/calendario/ical/tok-secreto.ics") == "/api/calendario/ical/<token>.ics"
    assert limpa_caminho("/api/historico/verificar/ABCD-EFGH") == "/api/historico/verificar/<codigo>"
    assert limpa_caminho("/api/turmas/123") == "/api/turmas/123"


def test_filtro_reescreve_registro_do_uvicorn():
    r = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "",
        0,
        '%s - "%s %s HTTP/%s" %d',
        ("10.0.0.1:5000", "GET", "/api/alunos?busca=Maria&token=zzz", "1.1", 200),
        None,
    )
    assert FiltroAcesso().filter(r) is True
    saida = r.getMessage()
    assert "Maria" not in saida and "zzz" not in saida and "/api/alunos" in saida and "10.0.0.1" in saida
