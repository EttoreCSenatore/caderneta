import re

from app import mail


def _link_token():
    return re.search(r"/convite/([\w-]+)", mail.outbox[-1].get_content()).group(1)


def test_ano_letivo_divide_bimestres(mundo, entrar):
    c = entrar("admin.a@teste.com")
    r = c.post(
        "/api/anos-letivos", json={"ano": 2027, "tipo_periodo": "bimestre", "inicio": "2027-02-01", "fim": "2027-12-10"}
    )
    assert r.status_code == 201
    p = r.json()["periodos"]
    assert [x["nome"] for x in p] == ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
    assert p[0]["inicio"] == "2027-02-01" and p[-1]["fim"] == "2027-12-10"
    assert (
        c.post(
            "/api/anos-letivos",
            json={"ano": 2027, "tipo_periodo": "bimestre", "inicio": "2027-02-01", "fim": "2027-12-10"},
        ).status_code
        == 409
    )


def test_cadastro_turma_disciplina_atribuicao_aluno(mundo, entrar):
    a, _ = mundo
    c = entrar("admin.a@teste.com")
    t = c.post("/api/turmas", json={"nome": "9º C", "serie": "9º ano"}).json()
    assert c.post("/api/turmas", json={"nome": "9º C", "serie": "9º ano"}).status_code == 409
    d = c.post("/api/disciplinas", json={"nome": "História"}).json()
    assert c.post("/api/disciplinas", json={"nome": "História"}).status_code == 409
    prof2 = a.usuarios["prof2"].id
    assert (
        c.post(
            f"/api/turmas/{t['id']}/atribuicoes", json={"disciplina_id": d["id"], "professor_id": str(prof2)}
        ).status_code
        == 201
    )
    mae = a.usuarios["mae"].id
    assert (
        c.post(
            f"/api/turmas/{t['id']}/atribuicoes", json={"disciplina_id": d["id"], "professor_id": str(mae)}
        ).status_code
        == 422
    )
    aluno = c.post(
        "/api/alunos", json={"nome": "Lia", "sobrenome": "Costa", "data_nascimento": "2012-08-09", "turma_id": t["id"]}
    ).json()
    assert aluno["turma"]["nome"] == "9º C"
    # prof2 agora vê a aluna
    assert {x["nome"] for x in entrar("prof2.a@teste.com").get("/api/alunos").json()} == {"Lia"}


def test_convite_de_professor(mundo, entrar):
    adm = entrar("admin.a@teste.com")
    r = adm.post("/api/convites", json={"email": "nova.prof@teste.com", "nome": "Nova Prof", "papel": "professor"})
    assert r.status_code == 201
    token = _link_token()
    from tests.conftest import Cliente

    c = Cliente()
    info = c.get(f"/api/convites/abrir/{token}").json()
    assert info["escola"] == "Escola A" and info["conta_existente"] is False
    assert c.post(f"/api/convites/abrir/{token}", json={"senha": "123"}).status_code == 422
    assert c.post(f"/api/convites/abrir/{token}", json={"senha": "boa-senha-123"}).json()["status"] == "ok"
    assert c.get("/api/escola").status_code == 200
    assert Cliente().get(f"/api/convites/abrir/{token}").status_code == 404  # uso único
    assert Cliente().get("/api/convites/abrir/token-inventado").status_code == 404


def test_convite_de_responsavel_vincula_e_conta_existente_pede_senha(mundo, entrar):
    a, _ = mundo
    adm = entrar("admin.a@teste.com")
    maria = a.alunos["maria"].id
    # O professor também é pai da Maria: mesma conta, novo perfil.
    v = adm.post(
        f"/api/alunos/{maria}/responsaveis", json={"nome": "Prof A", "tipo": "pai", "email": "prof.a@teste.com"}
    ).json()
    assert adm.post(f"/api/responsaveis/{v['id']}/convite").status_code == 201
    token = _link_token()
    from tests.conftest import SENHA, Cliente

    c = Cliente()
    assert c.get(f"/api/convites/abrir/{token}").json()["conta_existente"] is True
    assert c.post(f"/api/convites/abrir/{token}", json={"senha": "errada-123"}).status_code == 401
    assert c.post(f"/api/convites/abrir/{token}", json={"senha": SENHA}).status_code == 200
    me = c.get("/api/auth/me").json()
    assert sorted(p["papel"] for p in me["perfis"]) == ["professor", "responsavel"]
    assert me["perfil_ativo"] is None  # dois perfis: o usuário escolhe
    resp = next(p for p in me["perfis"] if p["papel"] == "responsavel")
    c.post("/api/auth/perfil", json={"perfil_id": resp["id"]})
    assert {x["nome"] for x in c.get("/api/alunos").json()} == {"Maria"}


def test_convite_para_conta_existente_respeita_bloqueio(mundo, entrar):
    a, _ = mundo
    adm = entrar("admin.a@teste.com")
    v = adm.post(
        f"/api/alunos/{a.alunos['maria'].id}/responsaveis",
        json={"nome": "Prof A", "tipo": "pai", "email": "prof.a@teste.com"},
    ).json()
    adm.post(f"/api/responsaveis/{v['id']}/convite")
    token = _link_token()
    from tests.conftest import SENHA, Cliente

    c = Cliente()
    for _ in range(5):
        assert c.post(f"/api/convites/abrir/{token}", json={"senha": "errada-123"}).status_code == 401
    assert c.post(f"/api/convites/abrir/{token}", json={"senha": SENHA}).status_code == 429
    # e o login normal da conta também fica bloqueado
    assert c.post("/api/auth/login", json={"email": "prof.a@teste.com", "senha": SENHA}).status_code == 429
