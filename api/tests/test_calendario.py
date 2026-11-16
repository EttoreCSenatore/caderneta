"""M4: calendário (eventos, feriados, dias sem aula que bloqueiam a chamada, assinatura iCal)."""

from datetime import date

import pytest
from sqlalchemy import text

from app.calendario import feriados_sugeridos, ics, pascoa
from tests.conftest import Cliente


def _evento(c, **kw):
    body = {"tipo": "evento", "titulo": "Festa junina", "inicio": "2026-06-20", **kw}
    return c.post("/api/calendario/eventos", json=body)


def _lista(c, ini="2026-01-01", fim="2026-12-31", **p):
    return c.get("/api/calendario", params={"inicio": ini, "fim": fim, **p}).json()


def test_feriados_nacionais_e_moveis():
    assert pascoa(2026) == date(2026, 4, 5)
    assert pascoa(2025) == date(2025, 4, 20)
    f = {x["nome"]: x for x in feriados_sugeridos(2026)}
    assert f["Sexta-feira da Paixão"]["data"] == date(2026, 4, 3)
    assert f["Corpus Christi (ponto facultativo)"]["data"] == date(2026, 6, 4)
    assert f["Carnaval (segunda, ponto facultativo)"]["data"] == date(2026, 2, 16)
    assert f["Consciência Negra"]["nacional"] and f["Consciência Negra"]["base"] == "Lei 14.759/2023"
    assert sum(x["nacional"] for x in f.values()) == 9
    assert not f["Sexta-feira da Paixão"]["nacional"]  # a escola decide


def test_ics_escapa_e_dobra():
    txt = ics(
        "Cal",
        [
            {
                "id": "1",
                "titulo": "A, B; C\\D",
                "descricao": "x" * 200,
                "inicio": date(2026, 5, 1),
                "fim": date(2026, 5, 2),
            }
        ],
    )
    assert r"SUMMARY:A\, B\; C\\D" in txt
    assert "DTEND;VALUE=DATE:20260503" in txt  # fim exclusivo
    assert all(len(linha.encode()) <= 75 for linha in txt.split("\r\n"))
    assert txt.endswith("\r\n")


def test_permissoes(mundo, entrar):
    a, _ = mundo
    assert _evento(entrar("mae.a@teste.com")).status_code == 403
    prof = entrar("prof.a@teste.com")
    assert _evento(prof).status_code == 403  # escola toda: só equipe
    assert _evento(prof, turma_id=str(a.turma.id), tipo="sem_aula").status_code == 403
    assert _evento(prof, turma_id=str(a.turma2.id)).status_code == 404  # turma onde não leciona
    assert _evento(prof, turma_id=str(a.turma.id), tipo="prazo", titulo="Entrega do trabalho").status_code == 201
    assert _evento(entrar("coord.a@teste.com")).status_code == 201
    r = _evento(prof, turma_id=str(a.turma.id), inicio="2026-06-10", fim="2026-06-01")
    assert r.status_code == 422


def test_visibilidade_por_turma_e_avaliacoes(mundo, entrar, owner_engine):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    _evento(coord, titulo="Geral")
    _evento(coord, titulo="Só 7º A", turma_id=str(a.turma.id))
    _evento(coord, titulo="Só 8º B", turma_id=str(a.turma2.id))
    with owner_engine.begin() as db:
        atrib = db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar()
    prof = entrar("prof.a@teste.com")
    periodo = prof.get(f"/api/atribuicoes/{atrib}/diario").json()["periodos"][0]["id"]
    prof.post(
        f"/api/atribuicoes/{atrib}/avaliacoes",
        json={"periodo_id": periodo, "nome": "Prova 1", "peso": 1, "data": "2026-03-10"},
    )
    mae = entrar("mae.a@teste.com")
    titulos = {i["titulo"] for i in _lista(mae)}
    assert titulos == {"Geral", "Só 7º A", "Prova 1 · Matemática"}
    assert {i["titulo"] for i in _lista(coord)} >= {"Geral", "Só 8º B"}
    assert {i["titulo"] for i in _lista(prof)} == {"Geral", "Só 7º A", "Prova 1 · Matemática"}
    assert all(not i["editavel"] for i in _lista(mae))
    assert _lista(mae, ini="2026-07-01", fim="2026-07-31") == []
    assert mae.get("/api/calendario", params={"inicio": "2026-01-01", "fim": "2028-01-01"}).status_code == 422
    assert (
        mae.get(
            "/api/calendario", params={"inicio": "2026-01-01", "fim": "2026-02-01", "turma_id": str(a.turma2.id)}
        ).status_code
        == 404
    )


def test_edicao_so_do_autor_ou_equipe(mundo, entrar):
    a, _ = mundo
    prof, coord = entrar("prof.a@teste.com"), entrar("coord.a@teste.com")
    eid = _evento(prof, turma_id=str(a.turma.id)).json()["id"]
    body = {"tipo": "evento", "titulo": "Novo nome", "inicio": "2026-06-21", "turma_id": str(a.turma.id)}
    assert entrar("prof2.a@teste.com").patch(f"/api/calendario/eventos/{eid}", json=body).status_code == 404
    assert prof.patch(f"/api/calendario/eventos/{eid}", json=body).json()["titulo"] == "Novo nome"
    assert coord.delete(f"/api/calendario/eventos/{eid}").status_code == 204
    assert _lista(prof) == []


def test_sem_aula_bloqueia_chamada_e_notifica(mundo, entrar, owner_engine):
    a, _ = mundo
    with owner_engine.begin() as db:
        atrib = db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar()
    prof, coord, mae = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("mae.a@teste.com")
    aula = {"data": "2026-03-10", "quantidade": 1, "registros": []}
    assert prof.post(f"/api/atribuicoes/{atrib}/aulas", json=aula).status_code == 201
    r = _evento(coord, tipo="sem_aula", titulo="Conselho de classe", inicio="2026-03-10", fim="2026-03-11")
    assert r.status_code == 201 and r.json()["aulas_ja_registradas"] == 1
    assert [n["tipo"] for n in mae.get("/api/notificacoes").json()] == ["calendario"]
    r = prof.post(f"/api/atribuicoes/{atrib}/aulas", json={**aula, "data": "2026-03-11"})
    assert r.status_code == 409 and "Conselho de classe" in r.json()["detail"]
    assert prof.post(f"/api/atribuicoes/{atrib}/aulas", json={**aula, "data": "2026-03-12"}).status_code == 201
    # sem aula só da 8º B não bloqueia a 7º A
    _evento(coord, tipo="sem_aula", titulo="Passeio do 8º B", inicio="2026-03-12", turma_id=str(a.turma2.id))
    assert (
        prof.post(f"/api/atribuicoes/{atrib}/aulas", json={**aula, "data": "2026-03-12", "quantidade": 2}).status_code
        == 201
    )


def test_importar_feriados(mundo, entrar):
    coord, prof = entrar("coord.a@teste.com"), entrar("prof.a@teste.com")
    assert prof.get("/api/calendario/feriados-sugeridos", params={"ano": 2026}).status_code == 403
    sug = coord.get("/api/calendario/feriados-sugeridos", params={"ano": 2026}).json()
    assert len(sug) == 13 and not any(s["ja_cadastrado"] for s in sug)
    datas = [s["data"] for s in sug if s["nacional"]]
    assert coord.post("/api/calendario/feriados", json={"ano": 2026, "datas": datas}).json() == {"criados": 9}
    assert coord.post("/api/calendario/feriados", json={"ano": 2026, "datas": datas}).json() == {"criados": 0}
    assert coord.post("/api/calendario/feriados", json={"ano": 2026, "datas": ["2026-03-03"]}).status_code == 422
    assert all(x["tipo"] == "feriado" for x in _lista(coord))
    assert (
        sum(s["ja_cadastrado"] for s in coord.get("/api/calendario/feriados-sugeridos", params={"ano": 2026}).json())
        == 9
    )


def test_ical(mundo, entrar):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    _evento(coord, titulo="Reunião de pais", inicio=str(date.today()))
    _evento(coord, titulo="Prova do 8º B", inicio=str(date.today()), turma_id=str(a.turma2.id))
    _evento(coord, titulo="Excursão do 7º A", inicio=str(date.today()), turma_id=str(a.turma.id))
    mae = entrar("mae.a@teste.com")
    assert mae.get("/api/calendario-ical").json()["ativo"] is False
    url = mae.post("/api/calendario-ical").json()["url"]
    caminho = url.split("//", 1)[1].split("/", 1)[1]
    anonimo = Cliente()
    r = anonimo.get("/" + caminho)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/calendar")
    assert "SUMMARY:Reunião de pais" in r.text and "[7º A] Excursão do 7º A" in r.text
    assert "8º B" not in r.text and "João" not in r.text
    novo = mae.post("/api/calendario-ical").json()["url"]
    assert novo != url
    assert anonimo.get("/" + caminho).status_code == 404  # o link antigo morre
    assert anonimo.get("/" + novo.split("//", 1)[1].split("/", 1)[1]).status_code == 200
    assert mae.delete("/api/calendario-ical").status_code == 204
    assert anonimo.get("/" + novo.split("//", 1)[1].split("/", 1)[1]).status_code == 404
    assert anonimo.get("/api/calendario/ical/lixo.ics").status_code == 404


def test_ical_nao_cruza_escolas(mundo, entrar):
    a, b = mundo
    entrar("coord.a@teste.com").post(
        "/api/calendario/eventos", json={"tipo": "evento", "titulo": "Segredo A", "inicio": "2026-06-20"}
    )
    url = entrar("mae.b@teste.com").post("/api/calendario-ical").json()["url"]
    caminho = "/" + url.split("//", 1)[1].split("/", 1)[1]
    assert "Segredo A" not in Cliente().get(caminho).text
    trocado = caminho.replace(str(b.escola.id), str(a.escola.id))
    assert Cliente().get(trocado).status_code == 404
    assert (
        entrar("mae.b@teste.com").get("/api/calendario", params={"inicio": "2026-01-01", "fim": "2026-12-31"}).json()
        == []
    )


@pytest.mark.parametrize("papel", ["mae", "aluno"])
def test_leitores_nao_alteram(mundo, entrar, papel):
    a, _ = mundo
    eid = _evento(entrar("coord.a@teste.com")).json()["id"]
    c = entrar(f"{papel}.a@teste.com")
    assert c.delete(f"/api/calendario/eventos/{eid}").status_code == 404
