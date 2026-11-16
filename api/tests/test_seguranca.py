"""Revisão de segurança (M8.1): cobertura de autenticação, limites de taxa, reuso de TOTP, conta e cabeçalhos."""

import pyotp
from fastapi.routing import APIRoute

from app import deps
from app.config import get_settings
from app.main import ROTEADORES
from tests.conftest import SENHA, TOTP, Cliente

# Rotas que, de propósito, não exigem sessão. Qualquer rota nova fora desta lista sem login reprova o teste.
PUBLICAS = {
    ("POST", "/auth/login"),
    ("POST", "/auth/senha/esqueci"),
    ("POST", "/auth/senha/redefinir"),
    ("GET", "/convites/abrir/{token}"),
    ("POST", "/convites/abrir/{token}"),
    ("GET", "/calendario/ical/{token}.ics"),  # link secreto
    ("GET", "/historico/verificar/{codigo}"),  # conferência pública do histórico
    ("GET", "/legal/{doc}"),  # política de privacidade e termos: texto público
}


def _chamadas(dep, acc):
    for s in dep.dependencies:
        acc.add(s.call)
        _chamadas(s, acc)
    return acc


def test_toda_rota_exige_sessao_exceto_as_publicas_conhecidas():
    sem_sessao = set()
    total = 0
    for mod in ROTEADORES:
        for r in mod.router.routes:
            if isinstance(r, APIRoute):
                total += 1
                if deps.sessao_parcial not in _chamadas(r.dependant, set()):
                    for m in r.methods:
                        sem_sessao.add((m, mod.router.prefix + r.path))
    assert total > 100  # garante que o teste está mesmo enxergando as rotas
    assert sem_sessao == {
        (m, p.replace("/auth/", "/auth/auth/", 1) if p.startswith("/auth/") else p) for m, p in PUBLICAS
    }


def test_rotas_com_papel_continuam_protegidas_sem_login(mundo):
    c = Cliente()
    for caminho in ("/api/alunos", "/api/turmas", "/api/avisos", "/api/escola", "/api/desligados"):
        assert c.get(caminho).status_code == 401, caminho


# --- limites de taxa -----------------------------------------------------------------------------------------


def test_login_limitado_por_ip(mundo, monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit", True)
    c = Cliente()
    codigos = [
        c.post("/api/auth/login", json={"email": f"x{i}@teste.com", "senha": "errada-123"}).status_code
        for i in range(32)
    ]
    assert codigos[:30] == [401] * 30
    assert codigos[30:] == [429, 429]


def test_esqueci_senha_limita_envios_por_email_sem_revelar(mundo, monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit", True)
    c = Cliente()
    for _ in range(6):
        assert c.post("/api/auth/senha/esqueci", json={"email": "prof.a@teste.com"}).status_code == 204
    from app import mail

    assert len(mail.outbox) == 3


def test_verificacao_publica_do_historico_limitada(mundo, monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit", True)
    c = Cliente()
    st = [c.get("/api/historico/verificar/AAAA-BBBB-CCCC").status_code for _ in range(22)]
    assert st[:20] == [404] * 20
    assert st[20:] == [429, 429]


# --- TOTP ----------------------------------------------------------------------------------------------------


def test_codigo_totp_nao_pode_ser_reutilizado(mundo, monkeypatch):
    monkeypatch.setattr(get_settings(), "totp_anti_reuso", True)
    codigo = pyotp.TOTP(TOTP).now()
    c1 = Cliente()
    assert c1.post("/api/auth/login", json={"email": "admin.a@teste.com", "senha": SENHA}).status_code == 200
    assert c1.post("/api/auth/codigo", json={"codigo": codigo}).status_code == 200
    c2 = Cliente()
    assert c2.post("/api/auth/login", json={"email": "admin.a@teste.com", "senha": SENHA}).status_code == 200
    r = c2.post("/api/auth/codigo", json={"codigo": codigo})
    assert r.status_code == 401
    assert "já usado" in r.json()["detail"]


# --- conta: trocar senha e encerrar sessões ----------------------------------------------------------------


def test_alterar_senha_exige_a_atual_e_derruba_outras_sessoes(mundo, entrar):
    a, b = entrar("prof.a@teste.com"), entrar("prof.a@teste.com")
    nova = "outra-senha-forte-456"
    assert a.post("/api/auth/senha/alterar", json={"senha_atual": "errada-000", "senha_nova": nova}).status_code == 400
    assert a.post("/api/auth/senha/alterar", json={"senha_atual": SENHA, "senha_nova": "123"}).status_code == 422
    assert a.post("/api/auth/senha/alterar", json={"senha_atual": SENHA, "senha_nova": SENHA}).status_code == 422
    assert a.post("/api/auth/senha/alterar", json={"senha_atual": SENHA, "senha_nova": nova}).status_code == 204
    assert a.get("/api/auth/me").status_code == 200  # a sessão atual continua
    assert b.get("/api/auth/me").status_code == 401  # a outra foi encerrada
    assert Cliente().post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": SENHA}).status_code == 401
    assert Cliente().post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": nova}).status_code == 200


def test_lista_de_sessoes_e_sair_de_todos(mundo, entrar):
    a, b = entrar("mae.a@teste.com"), entrar("mae.a@teste.com")
    lista = a.get("/api/auth/sessoes").json()
    assert len(lista) == 2 and sum(s["atual"] for s in lista) == 1
    assert "token" not in lista[0] and "token_hash" not in lista[0]
    assert a.post("/api/auth/sair-de-todos").status_code == 204
    assert a.get("/api/auth/me").status_code == 401
    assert b.get("/api/auth/me").status_code == 401


# --- cabeçalhos -----------------------------------------------------------------------------------------------


def test_cabecalhos_de_seguranca(mundo, monkeypatch):
    r = Cliente().get("/api/saude")
    assert r.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"
    assert "strict-transport-security" not in r.headers  # só com cookie seguro (produção)
    monkeypatch.setattr(get_settings(), "cookie_secure", True)
    r = Cliente().get("/api/saude")
    assert "max-age=" in r.headers["strict-transport-security"]
