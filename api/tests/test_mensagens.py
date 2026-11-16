"""M3: mensagens individuais (conversas escola ↔ responsáveis)."""

from sqlalchemy import text


def _inicia(c, aluno, **kw):
    return c.post("/api/conversas", json={"aluno_id": str(aluno.id), "assunto": "Desempenho", "corpo": "Olá!", **kw})


def test_professor_inicia_e_familia_responde(mundo, entrar):
    a, _ = mundo
    prof, mae = entrar("prof.a@teste.com"), entrar("mae.a@teste.com")
    r = _inicia(prof, a.alunos["joao"])
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert mae.get("/api/mensagens-pendentes").json() == {"nao_lidas": 1}
    assert prof.get("/api/mensagens-pendentes").json() == {"nao_lidas": 0}  # quem enviou não tem pendência
    lista = mae.get("/api/conversas").json()
    assert lista[0]["nao_lida"] and lista[0]["previa"] == "Olá!"
    d = mae.get(f"/api/conversas/{cid}").json()
    assert [m["corpo"] for m in d["mensagens"]] == ["Olá!"] and not d["mensagens"][0]["minha"]
    assert mae.get("/api/mensagens-pendentes").json() == {"nao_lidas": 0}
    assert mae.post(f"/api/conversas/{cid}/mensagens", json={"corpo": "Obrigada, professor."}).status_code == 201
    assert prof.get("/api/mensagens-pendentes").json() == {"nao_lidas": 1}
    d = prof.get(f"/api/conversas/{cid}").json()
    assert len(d["mensagens"]) == 2 and d["mensagens"][1]["autor"] == "Mae.A"


def test_quem_pode_iniciar(mundo, entrar):
    a, _ = mundo
    assert _inicia(entrar("aluno.a@teste.com"), a.alunos["joao"]).status_code == 403
    prof = entrar("prof.a@teste.com")
    assert _inicia(prof, a.alunos["pedro"]).status_code == 404  # aluno de outra turma
    assert _inicia(entrar("prof2.a@teste.com"), a.alunos["joao"]).status_code == 404  # sem atribuição
    assert _inicia(entrar("coord.a@teste.com"), a.alunos["pedro"]).status_code == 201


def test_familia_inicia_com_professor_da_turma(mundo, entrar):
    a, _ = mundo
    mae = entrar("mae.a@teste.com")
    assert _inicia(mae, a.alunos["joao"]).status_code == 422  # precisa escolher o professor
    assert _inicia(mae, a.alunos["joao"], professor_id=str(a.usuarios["prof2"].id)).status_code == 422
    assert (
        _inicia(mae, a.alunos["maria"], professor_id=str(a.usuarios["prof"].id)).status_code == 404
    )  # filha de outra família
    r = _inicia(mae, a.alunos["joao"], professor_id=str(a.usuarios["prof"].id))
    assert r.status_code == 201
    prof = entrar("prof.a@teste.com")
    assert prof.get("/api/mensagens-pendentes").json() == {"nao_lidas": 1}
    assert prof.get("/api/conversas").json()[0]["aluno"].startswith("João")


def test_privacidade_e_supervisao(mundo, entrar, owner_engine):
    a, _ = mundo
    prof = entrar("prof.a@teste.com")
    cid = _inicia(prof, a.alunos["joao"]).json()["id"]
    assert entrar("prof2.a@teste.com").get(f"/api/conversas/{cid}").status_code == 404
    assert entrar("prof2.a@teste.com").get("/api/conversas").json() == []
    assert entrar("aluno.a@teste.com").get(f"/api/conversas/{cid}").status_code == 404
    coord = entrar("coord.a@teste.com")
    assert coord.get(f"/api/conversas/{cid}").status_code == 200
    with owner_engine.begin() as db:
        n = db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'conversa.supervisao'")).scalar()
    assert n == 1


def test_isolamento_entre_escolas(mundo, entrar):
    a, b = mundo
    cid = _inicia(entrar("prof.a@teste.com"), a.alunos["joao"]).json()["id"]
    assert entrar("mae.b@teste.com").get(f"/api/conversas/{cid}").status_code == 404
    assert entrar("coord.b@teste.com").get(f"/api/conversas/{cid}").status_code == 404
    assert entrar("coord.b@teste.com").post(f"/api/conversas/{cid}/mensagens", json={"corpo": "x"}).status_code == 404
