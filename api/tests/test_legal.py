"""M8.3: textos legais públicos, confirmação (ciência) por versão e encarregado da escola."""

from sqlalchemy import text

from app import legal
from tests.conftest import Cliente


def test_textos_sao_publicos_e_tem_versao_e_status():
    c = Cliente()
    for doc in ("privacidade", "termos"):
        r = c.get(f"/api/legal/{doc}")
        assert r.status_code == 200
        d = r.json()
        assert d["versao"] and d["titulo"] and d["status"] in ("rascunho", "vigente")
        assert d["texto"].startswith("# ")
    assert c.get("/api/legal/outro").status_code == 404


def test_texto_diz_o_que_o_sistema_faz():
    """Garante que a política cita os pontos que o código de fato implementa (evita o texto ficar para trás)."""
    t = legal.carrega("privacidade")["texto"]
    for trecho in ("365 dias", "180 dias", "Meus dados", "15 dias", "5 anos", "cookie", "offline", "encarregado"):
        assert trecho in t, trecho


def test_pendentes_exige_login_e_lista_os_dois_textos(mundo, entrar):
    assert Cliente().get("/api/legal/pendentes").status_code == 401
    c = entrar("mae.a@teste.com")
    assert {p["doc"] for p in c.get("/api/legal/pendentes").json()} == {"privacidade", "termos"}


def test_aceitar_registra_por_versao_e_nao_pede_de_novo(mundo, entrar, owner_engine):
    c = entrar("mae.a@teste.com")
    pend = c.get("/api/legal/pendentes").json()
    assert (
        c.post(
            "/api/legal/aceitar", json={"aceites": [{"doc": p["doc"], "versao": p["versao"]} for p in pend]}
        ).status_code
        == 204
    )
    assert c.get("/api/legal/pendentes").json() == []
    # repetir não duplica
    assert (
        c.post(
            "/api/legal/aceitar", json={"aceites": [{"doc": pend[0]["doc"], "versao": pend[0]["versao"]}]}
        ).status_code
        == 204
    )
    with owner_engine.begin() as db:
        assert db.execute(text("SELECT count(*) FROM aceite_legal")).scalar() == 2
        assert db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'legal.aceite'")).scalar() == 2


def test_aceitar_versao_antiga_e_recusado_e_nova_versao_pede_de_novo(mundo, entrar, monkeypatch):
    c = entrar("mae.a@teste.com")
    assert (
        c.post("/api/legal/aceitar", json={"aceites": [{"doc": "termos", "versao": "1999-01-01.0"}]}).status_code == 409
    )
    pend = c.get("/api/legal/pendentes").json()
    c.post("/api/legal/aceitar", json={"aceites": [{"doc": p["doc"], "versao": p["versao"]} for p in pend]})
    assert c.get("/api/legal/pendentes").json() == []
    novo = dict(legal.carrega("termos"), versao="2099-01-01.1")
    monkeypatch.setattr("app.routers.legal.carrega", lambda d: novo if d == "termos" else legal.carrega(d))
    assert [p["doc"] for p in c.get("/api/legal/pendentes").json()] == ["termos"]


def test_aceite_e_de_cada_pessoa(mundo, entrar):
    a = entrar("mae.a@teste.com")
    a.post(
        "/api/legal/aceitar",
        json={"aceites": [{"doc": p["doc"], "versao": p["versao"]} for p in a.get("/api/legal/pendentes").json()]},
    )
    assert len(entrar("prof.a@teste.com").get("/api/legal/pendentes").json()) == 2


def test_encarregado_so_a_direcao_define_e_todos_veem(mundo, entrar):
    admin = entrar("admin.a@teste.com")
    corpo = {"encarregado_nome": "Dra. Helena Dias", "encarregado_email": "privacidade@escola-a.com.br"}
    assert entrar("coord.a@teste.com").patch("/api/escola", json=corpo).status_code == 403
    assert admin.patch("/api/escola", json=corpo).status_code == 200
    assert admin.patch("/api/escola", json={"encarregado_email": "nao-e-email"}).status_code == 422
    for quem in ("mae.a@teste.com", "prof.a@teste.com", "aluno.a@teste.com"):
        assert entrar(quem).get("/api/escola").json()["encarregado"] == {
            "nome": "Dra. Helena Dias",
            "email": "privacidade@escola-a.com.br",
        }


def test_operadora_da_instalacao_aparece_nos_textos(monkeypatch):
    from app.config import get_settings

    assert "{{operadora}}" not in legal.carrega("privacidade")["texto"]
    assert "INFORMAR NA CONFIGURAÇÃO" in legal.carrega("privacidade")["texto"]  # sem configuração: lembrete visível
    monkeypatch.setattr(get_settings(), "operadora_nome", "Tecnologia Exemplo Ltda.")
    monkeypatch.setattr(get_settings(), "operadora_contato", "contato@exemplo.com.br")
    for doc in ("privacidade", "termos"):
        t = Cliente().get(f"/api/legal/{doc}").json()["texto"]
        assert "**Tecnologia Exemplo Ltda.** (contato@exemplo.com.br)" in t
        assert "{{" not in t
