import re

import pyotp

from app import mail
from tests.conftest import SENHA, TOTP, Cliente


def test_login_errado_nao_revela_usuario(mundo):
    c = Cliente()
    r1 = c.post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": "errada-123"})
    r2 = c.post("/api/auth/login", json={"email": "ninguem@teste.com", "senha": "errada-123"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


def test_bloqueio_apos_falhas(mundo):
    c = Cliente()
    for _ in range(5):
        assert c.post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": "errada-123"}).status_code == 401
    r = c.post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": SENHA})
    assert r.status_code == 429


def test_professor_entra_e_perfil_unico_e_selecionado(mundo, entrar):
    c = entrar("prof.a@teste.com")
    me = c.get("/api/auth/me").json()
    assert me["status"] == "ok"
    assert me["perfil_ativo"] == me["perfis"][0]["id"]
    assert c.get("/api/escola").json()["nome"] == "Escola A"


def test_csrf_exige_cabecalho(mundo):
    from fastapi.testclient import TestClient

    from app.main import app

    r = TestClient(app).post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": SENHA})
    assert r.status_code == 403


def test_admin_precisa_do_codigo(mundo):
    c = Cliente()
    r = c.post("/api/auth/login", json={"email": "admin.a@teste.com", "senha": SENHA})
    assert r.json()["status"] == "codigo"
    assert c.get("/api/escola").status_code == 401
    assert c.post("/api/auth/codigo", json={"codigo": "000000"}).status_code == 401
    assert c.post("/api/auth/codigo", json={"codigo": pyotp.TOTP(TOTP).now()}).json()["status"] == "ok"
    assert c.get("/api/escola").status_code == 200


def test_equipe_sem_2fa_precisa_configurar(mundo, owner_engine):
    from sqlalchemy import text

    with owner_engine.begin() as db:
        db.execute(text("UPDATE usuario SET totp_ativo=false, totp_secret_enc=NULL WHERE email='coord.a@teste.com'"))
    c = Cliente()
    r = c.post("/api/auth/login", json={"email": "coord.a@teste.com", "senha": SENHA})
    assert r.json()["status"] == "configurar_2fa"
    assert c.get("/api/alunos").status_code == 403
    secret = c.post("/api/auth/2fa/iniciar").json()["secret"]
    assert c.post("/api/auth/2fa/ativar", json={"codigo": "123456"}).status_code == 400
    assert c.post("/api/auth/2fa/ativar", json={"codigo": pyotp.TOTP(secret).now()}).json()["status"] == "ok"
    assert c.get("/api/alunos").status_code == 200


def test_logout_invalida_sessao(mundo, entrar):
    c = entrar("prof.a@teste.com")
    assert c.post("/api/auth/logout").status_code == 204
    assert c.get("/api/auth/me").status_code == 401


def test_recuperacao_de_senha(mundo, entrar):
    antigo = entrar("mae.a@teste.com")
    c = Cliente()
    assert c.post("/api/auth/senha/esqueci", json={"email": "mae.a@teste.com"}).status_code == 204
    assert c.post("/api/auth/senha/esqueci", json={"email": "nao.existe@teste.com"}).status_code == 204
    assert len(mail.outbox) == 1
    token = re.search(r"token=([\w-]+)", mail.outbox[0].get_content()).group(1)
    assert c.post("/api/auth/senha/redefinir", json={"token": token, "senha": "curta"}).status_code == 422
    assert c.post("/api/auth/senha/redefinir", json={"token": token, "senha": "nova-senha-456"}).status_code == 204
    assert c.post("/api/auth/senha/redefinir", json={"token": token, "senha": "outra-senha-789"}).status_code == 400
    assert antigo.get("/api/auth/me").status_code == 401  # sessões antigas caem
    entrar("mae.a@teste.com", "nova-senha-456")
