"""M3: avisos (escola/turma), agendamento, ciente e painel de leitura."""

from datetime import UTC, datetime, timedelta


def _novo(c, **kw):
    r = c.post("/api/avisos", json={"titulo": "Reunião", "corpo": "Sexta, 19h.", **kw})
    return r


def test_permissoes_de_envio(mundo, entrar):
    a, _ = mundo
    assert _novo(entrar("mae.a@teste.com")).status_code == 403
    prof = entrar("prof.a@teste.com")
    assert _novo(prof).status_code == 403  # escola toda: só equipe
    assert _novo(prof, turma_id=str(a.turma2.id)).status_code == 404  # turma onde não leciona
    assert _novo(prof, turma_id=str(a.turma.id)).status_code == 201
    assert _novo(entrar("coord.a@teste.com")).status_code == 201


def test_publico_por_escopo_e_agendamento(mundo, entrar):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    _novo(coord, titulo="Geral")
    _novo(coord, titulo="Só 8º B", turma_id=str(a.turma2.id))
    _novo(coord, titulo="Futuro", publicar_em=(datetime.now(UTC) + timedelta(days=2)).isoformat())
    titulos = {x["titulo"] for x in entrar("mae.a@teste.com").get("/api/avisos").json()}
    assert titulos == {"Geral"}  # filha na 7º A; o do futuro ainda não saiu
    assert {x["titulo"] for x in coord.get("/api/avisos").json()} == {"Geral", "Só 8º B", "Futuro"}


def test_ciente_e_painel(mundo, entrar):
    a, _ = mundo
    prof = entrar("prof.a@teste.com")
    aid = _novo(prof, turma_id=str(a.turma.id), exige_ciente=True).json()["id"]
    mae, aluno = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com")
    assert mae.get("/api/avisos-pendentes").json() == {"nao_lidos": 1}
    r = mae.post(f"/api/avisos/{aid}/lido").json()
    assert r["lido"] and not r["ciente"]
    assert mae.post(f"/api/avisos/{aid}/lido", params={"ciente": True}).json()["ciente"] is True
    assert mae.get("/api/avisos-pendentes").json() == {"nao_lidos": 0}
    p = prof.get(f"/api/avisos/{aid}/painel").json()
    assert (p["total"], p["lidos"], p["cientes"]) == (2, 1, 1)  # mãe + conta do aluno; pai restrito fora
    assert mae.get(f"/api/avisos/{aid}/painel").status_code == 404
    aluno.post(f"/api/avisos/{aid}/lido")
    assert prof.get(f"/api/avisos/{aid}/painel").json()["lidos"] == 2
    assert entrar("prof2.a@teste.com").get(f"/api/avisos/{aid}/painel").status_code == 404


def test_isolamento_entre_escolas(mundo, entrar):
    a, b = mundo
    aid = _novo(entrar("coord.a@teste.com")).json()["id"]
    outra = entrar("mae.b@teste.com")
    assert outra.get("/api/avisos").json() == []
    assert outra.post(f"/api/avisos/{aid}/lido").status_code == 404
    assert entrar("coord.b@teste.com").get(f"/api/avisos/{aid}/painel").status_code == 404


def test_arquivar(mundo, entrar):
    coord = entrar("coord.a@teste.com")
    aid = _novo(coord).json()["id"]
    assert coord.post(f"/api/avisos/{aid}/arquivar").status_code == 200
    assert coord.get("/api/avisos").json() == []
    assert len(coord.get("/api/avisos", params={"arquivados": True}).json()) == 1
