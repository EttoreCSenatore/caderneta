"""M6.2: anotações sobre o aluno (tipos, visibilidade, versões, remoção e passar o bastão entre anos)."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.retencao import elimina_vencidos


def _nova(c, aluno, tipo="pedagogica", corpo="Melhora com atividades em dupla.", **kw):
    return c.post(f"/api/alunos/{aluno.id}/anotacoes", json={"tipo": tipo, "corpo": corpo, **kw})


def _corpos(c, aluno, **p):
    r = c.get(f"/api/alunos/{aluno.id}/anotacoes", params=p)
    assert r.status_code == 200, r.text
    return {x["corpo"] for x in r.json()}


def _auditoria(owner_engine, acao):
    with owner_engine.begin() as db:
        return db.execute(text("SELECT count(*) FROM auditoria WHERE acao = :a"), {"a": acao}).scalar()


def test_quem_pode_criar_cada_tipo(mundo, entrar):
    a, _ = mundo
    joao = a.alunos["joao"]
    for leitor in ("mae.a@teste.com", "aluno.a@teste.com"):
        assert _nova(entrar(leitor), joao).status_code == 403
    prof, coord = entrar("prof.a@teste.com"), entrar("coord.a@teste.com")
    for tipo in ("pedagogica", "ocorrencia", "elogio"):
        assert _nova(prof, joao, tipo).status_code == 201
    assert _nova(prof, joao, "reservada").status_code == 403
    assert _nova(coord, joao, "reservada").status_code == 201
    assert _nova(entrar("prof2.a@teste.com"), joao).status_code == 404  # não leciona para o João
    assert _nova(prof, a.alunos["pedro"]).status_code == 404  # aluno de outra turma
    assert _nova(prof, joao, corpo="").status_code == 422
    # a marca de visibilidade só vale para ocorrência
    r = _nova(prof, joao, "pedagogica", "x", visivel_responsaveis=True).json()
    assert r["visivel_responsaveis"] is False


def test_matriz_de_visibilidade(mundo, entrar, owner_engine):
    a, _ = mundo
    joao = a.alunos["joao"]
    prof, coord, mae = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("mae.a@teste.com")
    _nova(coord, joao, "pedagogica", "PED")
    _nova(coord, joao, "ocorrencia", "OCO-INTERNA")
    _nova(coord, joao, "ocorrencia", "OCO-FAMILIA", visivel_responsaveis=True)
    _nova(coord, joao, "elogio", "ELO")
    _nova(coord, joao, "reservada", "RES")
    _nova(prof, joao, "ocorrencia", "OCO-DO-PROF")
    assert _corpos(coord, joao) == {"PED", "OCO-INTERNA", "OCO-FAMILIA", "ELO", "RES", "OCO-DO-PROF"}
    assert _corpos(prof, joao) == {"PED", "ELO", "OCO-DO-PROF"}  # não vê ocorrência alheia nem reservada
    assert _corpos(mae, joao) == {"OCO-FAMILIA", "ELO"}
    assert _corpos(entrar("aluno.a@teste.com"), joao) == set()
    assert _corpos(coord, joao, tipo="elogio") == {"ELO"}
    assert entrar("prof2.a@teste.com").get(f"/api/alunos/{joao.id}/anotacoes").status_code == 404
    assert entrar("mae.a@teste.com").get(f"/api/alunos/{a.alunos['maria'].id}/anotacoes").status_code == 404
    # a família não recebe dados internos
    item = mae.get(f"/api/alunos/{joao.id}/anotacoes").json()[0]
    assert "versao" not in item and "removida" not in item
    # só a leitura da reservada pela equipe é auditada
    assert _auditoria(owner_engine, "anotacao.reservada_lida") == 1  # a primeira listagem da coordenação
    prof.get(f"/api/alunos/{joao.id}/anotacoes")
    assert _auditoria(owner_engine, "anotacao.reservada_lida") == 1


def test_versoes_ao_editar(mundo, entrar):
    a, _ = mundo
    joao = a.alunos["joao"]
    prof, coord, mae = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("mae.a@teste.com")
    nid = _nova(prof, joao, corpo="Primeira versão").json()["id"]
    assert prof.patch(f"/api/anotacoes/{nid}", json={"corpo": "Segunda versão"}).json()["versao"] == 2
    r = coord.patch(f"/api/anotacoes/{nid}", json={"corpo": "Terceira versão", "tipo": "elogio"}).json()
    assert (r["versao"], r["tipo"], r["corpo"]) == (3, "elogio", "Terceira versão")
    v = prof.get(f"/api/anotacoes/{nid}/versoes").json()
    assert [x["versao"] for x in v] == [3, 2, 1]
    assert [x["corpo"] for x in v] == ["Terceira versão", "Segunda versão", "Primeira versão"]
    assert v[0]["editado_por"] == "Coord.A" and v[2]["tipo"] == "pedagogica"
    assert mae.get(f"/api/anotacoes/{nid}/versoes").status_code == 404
    assert mae.patch(f"/api/anotacoes/{nid}", json={"corpo": "x"}).status_code == 404
    assert prof.patch(f"/api/anotacoes/{nid}", json={"tipo": "reservada"}).status_code == 403
    deles = _nova(coord, joao, corpo="Da coordenação").json()["id"]
    assert prof.patch(f"/api/anotacoes/{deles}", json={"corpo": "tentativa"}).status_code == 404
    assert prof.get(f"/api/anotacoes/{deles}/versoes").status_code == 404


def test_avisos_a_familia_e_a_equipe(mundo, entrar):
    a, _ = mundo
    joao = a.alunos["joao"]
    prof, coord, mae = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("mae.a@teste.com")
    _nova(prof, joao, "pedagogica", "interna")
    _nova(prof, joao, "ocorrencia", "oculta")
    assert mae.get("/api/notificacoes").json() == []  # nada visível para a família, nada de aviso
    notifs_equipe = [n["titulo"] for n in coord.get("/api/notificacoes").json()]
    assert notifs_equipe == ["Nova ocorrência registrada por professor"]
    nid = _nova(prof, joao, "ocorrencia", "SEGREDO-DO-TEXTO", visivel_responsaveis=True).json()["id"]
    (n,) = [x for x in mae.get("/api/notificacoes").json()]
    assert n["titulo"] == "Nova ocorrência registrada" and "SEGREDO" not in n["corpo"] + n["titulo"]
    assert "Silva A" in n["corpo"]
    _nova(prof, joao, "elogio", "Parabéns!")
    assert [x["titulo"] for x in mae.get("/api/notificacoes").json()][0] == "Novo elogio"
    oculta = [x for x in prof.get(f"/api/alunos/{joao.id}/anotacoes").json() if x["corpo"] == "oculta"][0]["id"]
    prof.patch(f"/api/anotacoes/{oculta}", json={"visivel_responsaveis": True})  # passa a ser visível: avisa
    assert len(mae.get("/api/notificacoes").json()) == 3
    prof.patch(f"/api/anotacoes/{nid}", json={"corpo": "ajuste de texto"})  # já era visível: não avisa de novo
    assert len(mae.get("/api/notificacoes").json()) == 3


def test_remover_e_eliminar_depois_da_carencia(mundo, entrar, owner_engine):
    a, _ = mundo
    joao = a.alunos["joao"]
    prof, coord, mae = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("mae.a@teste.com")
    nid = _nova(prof, joao, "elogio", "Elogio removido").json()["id"]
    assert mae.get(f"/api/alunos/{joao.id}/anotacoes").json()[0]["corpo"] == "Elogio removido"
    assert entrar("prof2.a@teste.com").delete(f"/api/anotacoes/{nid}").status_code == 404
    assert prof.delete(f"/api/anotacoes/{nid}").status_code == 204
    assert _corpos(prof, joao) == set() and _corpos(mae, joao) == set()
    removida = coord.get(f"/api/alunos/{joao.id}/anotacoes").json()[0]
    assert removida["removida"] is True and removida["editavel"] is False
    assert prof.get(f"/api/anotacoes/{nid}/versoes").status_code == 404
    assert prof.patch(f"/api/anotacoes/{nid}", json={"corpo": "ressuscitar"}).status_code == 404
    with Session(owner_engine) as db, db.begin():
        assert elimina_vencidos(db)["anotacoes"] == 0  # ainda na carência
        db.execute(text("UPDATE anotacao SET removida_em = now() - interval '31 days'"))
    with Session(owner_engine) as db, db.begin():
        assert elimina_vencidos(db)["anotacoes"] == 1
    with owner_engine.begin() as db:
        assert db.execute(text("SELECT count(*) FROM anotacao")).scalar() == 0
        assert db.execute(text("SELECT count(*) FROM anotacao_versao")).scalar() == 0
        assert db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'retencao.eliminar'")).scalar() == 1


def test_isolamento_entre_escolas(mundo, entrar):
    a, b = mundo
    nid = _nova(entrar("coord.a@teste.com"), a.alunos["joao"], "elogio").json()["id"]
    outra = entrar("coord.b@teste.com")
    assert outra.get(f"/api/alunos/{a.alunos['joao'].id}/anotacoes").status_code == 404
    assert outra.patch(f"/api/anotacoes/{nid}", json={"corpo": "x"}).status_code == 404
    assert outra.get(f"/api/anotacoes/{nid}/versoes").status_code == 404
    assert _nova(outra, a.alunos["joao"]).status_code == 404


def test_passar_o_bastao_entre_anos(mundo, entrar, owner_engine):
    a, _ = mundo
    joao = a.alunos["joao"]
    prof, coord, admin = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("admin.a@teste.com")
    _nova(prof, joao, "pedagogica", "PED-2026")
    _nova(prof, joao, "ocorrencia", "OCO-2026")
    _nova(coord, joao, "reservada", "RES-2026")
    with owner_engine.begin() as db:
        periodo = str(db.execute(text("SELECT id FROM periodo")).scalar())
        ano26 = str(db.execute(text("SELECT id FROM ano_letivo")).scalar())
    assert coord.post(f"/api/periodos/{periodo}/fechamento", json={"fechado": True}).status_code == 200
    ano27 = admin.post(
        "/api/anos-letivos", json={"ano": 2027, "tipo_periodo": "bimestre", "inicio": "2027-02-01", "fim": "2027-12-10"}
    ).json()["id"]
    admin.post(f"/api/anos-letivos/{ano27}/turmas-do-ano", json={"de_ano_letivo_id": ano26})
    destino = {t["nome"]: t["id"] for t in admin.get("/api/turmas", params={"ano_letivo_id": ano27}).json()}["8º A"]
    item = {"aluno_id": str(joao.id), "resultado": "aprovado", "turma_destino_id": destino}
    r = coord.post(
        "/api/rematricula", json={"turma_origem_id": str(a.turma.id), "ano_destino_id": ano27, "itens": [item]}
    )
    assert r.status_code == 200
    admin.post(f"/api/anos-letivos/{ano26}/encerrar", json={"abrir_ano_id": ano27})
    # 2027: o professor (copiado para o 8º A) é "novo" para o aluno e recebe as anotações pedagógicas de 2026
    assert _corpos(prof, joao) == {"PED-2026", "OCO-2026"}  # a ocorrência é dele mesmo; a reservada continua fora
    nova = _nova(prof, joao, "pedagogica", "PED-2027").json()
    assert nova["ano"] == 2027
    anos = {x["corpo"]: x["ano"] for x in prof.get(f"/api/alunos/{joao.id}/anotacoes").json()}
    assert anos == {"PED-2026": 2026, "OCO-2026": 2026, "PED-2027": 2027}
    assert _corpos(coord, joao) >= {"RES-2026", "PED-2027"}
    # quem não é mais professor do aluno não vê nada
    with pytest.raises(AssertionError):
        _corpos(entrar("prof2.a@teste.com"), joao)
