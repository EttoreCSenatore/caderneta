"""M3: autorizações digitais (resposta por aluno, prazo, painel, isolamento)."""

from datetime import UTC, datetime, timedelta


def _novo(c, **kw):
    return c.post("/api/autorizacoes", json={"titulo": "Passeio ao museu", "descricao": "Sábado, 8h.", **kw})


def test_permissoes_de_criacao(mundo, entrar):
    a, _ = mundo
    assert _novo(entrar("mae.a@teste.com")).status_code == 403
    prof = entrar("prof.a@teste.com")
    assert _novo(prof).status_code == 403
    assert _novo(prof, turma_id=str(a.turma2.id)).status_code == 404
    assert _novo(prof, turma_id=str(a.turma.id)).status_code == 201


def test_resposta_painel_e_troca(mundo, entrar):
    a, _ = mundo
    prof = entrar("prof.a@teste.com")
    aid = _novo(prof, turma_id=str(a.turma.id)).json()["id"]
    mae = entrar("mae.a@teste.com")
    itens = mae.get("/api/autorizacoes").json()
    assert len(itens) == 1 and itens[0]["resposta"] is None
    joao = itens[0]["aluno_id"]
    url = f"/api/autorizacoes/{aid}/alunos/{joao}"
    assert mae.put(url, json={"autoriza": False, "observacao": "Viagem"}).status_code == 200
    assert mae.put(url, json={"autoriza": True}).json()["resposta"] == "autorizo"  # mudou de ideia
    assert mae.get("/api/autorizacoes").json()[0]["resposta"] == "autorizo"
    p = prof.get(f"/api/autorizacoes/{aid}/painel").json()
    assert (p["total"], p["autorizado"], p["negado"], p["pendente"]) == (2, 1, 0, 1)  # João e Maria
    lista = prof.get("/api/autorizacoes").json()[0]
    assert (lista["autorizados"], lista["pendentes"]) == (1, 1)
    assert mae.get(f"/api/autorizacoes/{aid}/painel").status_code == 404
    assert entrar("prof2.a@teste.com").get(f"/api/autorizacoes/{aid}/painel").status_code == 404
    # professor e aluno não respondem
    assert prof.put(url, json={"autoriza": True}).status_code == 403
    assert entrar("aluno.a@teste.com").get("/api/autorizacoes").json() == []


def test_so_responde_pelo_proprio_filho_e_publico(mundo, entrar):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    so_8b = _novo(coord, turma_id=str(a.turma2.id)).json()["id"]
    geral = _novo(coord).json()["id"]
    mae = entrar("mae.a@teste.com")
    assert [i["id"] for i in mae.get("/api/autorizacoes").json()] == [geral]  # filho é do 7º A
    joao = str(a.alunos["joao"].id)
    assert mae.put(f"/api/autorizacoes/{so_8b}/alunos/{joao}", json={"autoriza": True}).status_code == 404
    maria = str(a.alunos["maria"].id)  # filha de outra família
    assert mae.put(f"/api/autorizacoes/{geral}/alunos/{maria}", json={"autoriza": True}).status_code == 404


def test_prazo_encerrado(mundo, entrar):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    ontem = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    aid = _novo(coord, prazo=ontem).json()["id"]
    mae = entrar("mae.a@teste.com")
    item = mae.get("/api/autorizacoes").json()[0]
    assert item["encerrada"] is True
    r = mae.put(f"/api/autorizacoes/{aid}/alunos/{item['aluno_id']}", json={"autoriza": True})
    assert r.status_code == 409


def test_isolamento_e_arquivar(mundo, entrar):
    a, b = mundo
    coord = entrar("coord.a@teste.com")
    aid = _novo(coord).json()["id"]
    assert entrar("mae.b@teste.com").get("/api/autorizacoes").json() == []
    assert entrar("coord.b@teste.com").get(f"/api/autorizacoes/{aid}/painel").status_code == 404
    assert coord.post(f"/api/autorizacoes/{aid}/arquivar").status_code == 200
    assert coord.get("/api/autorizacoes").json() == []
