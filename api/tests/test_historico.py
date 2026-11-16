"""M6.1: virada de ano (turmas do novo ano, rematrícula em lote, encerramento) e linha do tempo."""

import pytest
from sqlalchemy import text

from app.routers.historico import avanca


def test_avanca_series_e_turmas():
    assert avanca("7º A") == "8º A"
    assert avanca("6º ano") == "7º ano"
    assert avanca("9º B") is None  # depois do 9º ano o aluno conclui
    assert avanca("Maternal") is None


@pytest.fixture
def virada(mundo, entrar, owner_engine):
    a, _ = mundo
    prof, coord, admin = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("admin.a@teste.com")
    with owner_engine.begin() as db:
        atrib = str(db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar())
    d = prof.get(f"/api/atribuicoes/{atrib}/diario").json()
    periodo = d["periodos"][0]["id"]
    mat = {x["nome"].split()[0]: x["matricula_id"] for x in d["alunos"]}
    av = prof.post(
        f"/api/atribuicoes/{atrib}/avaliacoes", json={"periodo_id": periodo, "nome": "Prova final", "peso": 1}
    ).json()["id"]
    notas = [{"matricula_id": mat["João"], "valor": 8}, {"matricula_id": mat["Maria"], "valor": 3}]
    assert prof.put(f"/api/avaliacoes/{av}/notas", json={"notas": notas}).status_code == 200
    anos = {x["ano"]: x["id"] for x in admin.get("/api/anos-letivos").json()}
    return {
        "a": a,
        "prof": prof,
        "coord": coord,
        "admin": admin,
        "periodo": periodo,
        "ano26": anos[2026],
        "av": av,
        "atrib": atrib,
    }


def _novo_ano(v, ano=2027):
    r = v["admin"].post(
        "/api/anos-letivos",
        json={"ano": ano, "tipo_periodo": "bimestre", "inicio": f"{ano}-02-01", "fim": f"{ano}-12-10"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _fecha_2026(v):
    assert v["coord"].post(f"/api/periodos/{v['periodo']}/fechamento", json={"fechado": True}).status_code == 200


def test_novo_ano_nasce_planejado_e_a_virada_abre_o_proximo(virada):
    v = virada
    ano27 = _novo_ano(v)
    anos = {x["ano"]: x["aberto"] for x in v["admin"].get("/api/anos-letivos").json()}
    assert anos == {2026: True, 2027: False}
    assert v["admin"].get("/api/escola").json()["ano_atual"]["ano"] == 2026
    _fecha_2026(v)
    assert (
        v["admin"].post(f"/api/anos-letivos/{v['ano26']}/encerrar", json={"abrir_ano_id": v["ano26"]}).status_code
        == 422
    )
    v["admin"].post(f"/api/anos-letivos/{v['ano26']}/encerrar", json={"abrir_ano_id": ano27})
    assert v["admin"].get("/api/escola").json()["ano_atual"]["ano"] == 2027


def test_turmas_do_novo_ano(virada):
    v = virada
    ano27 = _novo_ano(v)
    corpo = {"de_ano_letivo_id": v["ano26"]}
    assert v["coord"].post(f"/api/anos-letivos/{ano27}/turmas-do-ano", json=corpo).status_code == 403
    r = v["admin"].post(f"/api/anos-letivos/{ano27}/turmas-do-ano", json=corpo)
    assert sorted(r.json()["criadas"]) == ["8º A", "9º B"] and r.json()["sem_turma_seguinte"] == []
    assert v["admin"].post(f"/api/anos-letivos/{ano27}/turmas-do-ano", json=corpo).json()["criadas"] == []
    assert (
        v["admin"].post(f"/api/anos-letivos/{ano27}/turmas-do-ano", json={"de_ano_letivo_id": ano27}).status_code == 422
    )
    turmas = {t["nome"]: t for t in v["admin"].get("/api/turmas", params={"ano_letivo_id": ano27}).json()}
    assert {x["professor"] for x in turmas["8º A"]["atribuicoes"]} == {"Prof.A"}  # professor copiado


def test_encerrar_ano_exige_periodos_fechados(virada):
    v = virada
    assert v["admin"].post(f"/api/anos-letivos/{v['ano26']}/encerrar").status_code == 409
    _fecha_2026(v)
    assert v["coord"].post(f"/api/anos-letivos/{v['ano26']}/encerrar").status_code == 403
    assert v["admin"].post(f"/api/anos-letivos/{v['ano26']}/encerrar").json() == {
        "ano": 2026,
        "aberto": False,
        "ano_atual": None,
    }
    assert v["admin"].post(f"/api/anos-letivos/{v['ano26']}/encerrar").status_code == 409


def _prepara(v):
    """Ano 2027 com 8º A (copiado) e 7º A (para quem repete); 2026 com o período fechado."""
    _fecha_2026(v)
    ano27 = _novo_ano(v)
    v["admin"].post(f"/api/anos-letivos/{ano27}/turmas-do-ano", json={"de_ano_letivo_id": v["ano26"]})
    v["admin"].post("/api/turmas", json={"nome": "7º A", "serie": "7º ano", "ano_letivo_id": ano27})
    turmas = {t["nome"]: t["id"] for t in v["admin"].get("/api/turmas", params={"ano_letivo_id": ano27}).json()}
    return ano27, turmas


def test_previa_sugere_pelo_boletim(virada):
    v = virada
    ano27, turmas = _prepara(v)
    t7 = v["a"].turma.id
    p = v["coord"].get("/api/rematricula/previa", params={"turma_id": str(t7), "ano_destino_id": ano27}).json()
    por_nome = {x["nome"].split()[0]: x for x in p["alunos"]}
    assert por_nome["João"]["sugestao"] == "aprovado" and por_nome["João"]["turma_destino_sugerida"] == turmas["8º A"]
    assert por_nome["Maria"]["sugestao"] == "retido" and por_nome["Maria"]["turma_destino_sugerida"] == turmas["7º A"]
    assert por_nome["Maria"]["motivo"] == "Reprovado em alguma disciplina"
    assert p["ultima_serie"] is False and len(p["turmas_destino"]) == 3
    assert (
        v["prof"].get("/api/rematricula/previa", params={"turma_id": str(t7), "ano_destino_id": ano27}).status_code
        == 403
    )
    mesmo = v["coord"].get("/api/rematricula/previa", params={"turma_id": str(t7), "ano_destino_id": v["ano26"]})
    assert mesmo.status_code == 422


def test_previa_sem_fechamento_fica_pendente(virada):
    v = virada
    ano27 = _novo_ano(v)
    p = (
        v["coord"]
        .get("/api/rematricula/previa", params={"turma_id": str(v["a"].turma.id), "ano_destino_id": ano27})
        .json()
    )
    assert {x["sugestao"] for x in p["alunos"]} == {"pendente"}


def _item(aluno, resultado, destino=None):
    return {"aluno_id": str(aluno.id), "resultado": resultado, "turma_destino_id": destino}


def test_rematricula_em_lote(virada, owner_engine):
    v, a = virada, virada["a"]
    ano27, turmas = _prepara(v)
    corpo = {
        "turma_origem_id": str(a.turma.id),
        "ano_destino_id": ano27,
        "itens": [
            _item(a.alunos["joao"], "aprovado", turmas["8º A"]),
            _item(a.alunos["maria"], "retido", turmas["7º A"]),
        ],
    }
    assert v["prof"].post("/api/rematricula", json=corpo).status_code == 403
    assert v["coord"].post("/api/rematricula", json=corpo).json() == {
        "processados": 2,
        "aprovado": 1,
        "retido": 1,
        "transferido": 0,
        "concluiu": 0,
    }
    with owner_engine.begin() as db:
        sit = dict(
            db.execute(
                text(
                    "SELECT a.nome, m.situacao FROM matricula m JOIN aluno a ON a.id = m.aluno_id "
                    "JOIN ano_letivo y ON y.id = m.ano_letivo_id WHERE y.ano = 2026"
                )
            ).all()
        )
        novas = db.execute(
            text("SELECT count(*) FROM matricula m JOIN ano_letivo y ON y.id = m.ano_letivo_id WHERE y.ano = 2027")
        ).scalar()
        n = db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'rematricula'")).scalar()
    assert sit["João"] == "aprovado" and sit["Maria"] == "retido" and novas == 2 and n == 2
    # as notas de 2026 continuam intactas
    assert v["coord"].get(f"/api/avaliacoes/{v['av']}/notas") is not None
    assert v["coord"].post("/api/rematricula", json=corpo).status_code == 409  # já rematriculados


def test_rematricula_e_tudo_ou_nada(virada, owner_engine):
    v, a = virada, virada["a"]
    ano27, turmas = _prepara(v)
    base = {"turma_origem_id": str(a.turma.id), "ano_destino_id": ano27}
    ruins = [
        [_item(a.alunos["joao"], "aprovado", turmas["8º A"]), _item(a.alunos["maria"], "aprovado")],  # sem destino
        [_item(a.alunos["joao"], "transferido", turmas["8º A"])],  # transferido com destino
        [_item(a.alunos["pedro"], "aprovado", turmas["8º A"])],  # aluno de outra turma
        [_item(a.alunos["joao"], "aprovado", str(a.turma.id))],  # destino no ano errado
        [_item(a.alunos["joao"], "aprovado", turmas["8º A"]), _item(a.alunos["joao"], "retido", turmas["7º A"])],
    ]
    for itens in ruins:
        assert v["coord"].post("/api/rematricula", json={**base, "itens": itens}).status_code in (409, 422)
    with owner_engine.begin() as db:
        assert (
            db.execute(
                text("SELECT count(*) FROM matricula m JOIN ano_letivo y ON y.id = m.ano_letivo_id WHERE y.ano = 2027")
            ).scalar()
            == 0
        )


def test_transferencia_e_conclusao(virada, owner_engine):
    v, a = virada, virada["a"]
    ano27, _ = _prepara(v)
    corpo = {
        "turma_origem_id": str(a.turma.id),
        "ano_destino_id": ano27,
        "itens": [_item(a.alunos["joao"], "transferido"), _item(a.alunos["maria"], "concluiu")],
    }
    assert v["coord"].post("/api/rematricula", json=corpo).status_code == 200
    with owner_engine.begin() as db:
        sit = dict(db.execute(text("SELECT nome, situacao FROM aluno WHERE nome IN ('João', 'Maria')")).all())
    assert sit == {"João": "transferido", "Maria": "concluiu"}


def test_professor_do_ano_anterior_perde_o_acesso_apos_encerrar(virada):
    v, a = virada, virada["a"]
    ano27, turmas = _prepara(v)
    assert v["prof"].get(f"/api/alunos/{a.alunos['maria'].id}").status_code == 200
    corpo = {
        "turma_origem_id": str(a.turma.id),
        "ano_destino_id": ano27,
        "itens": [
            _item(a.alunos["joao"], "aprovado", turmas["8º A"]),
            _item(a.alunos["maria"], "retido", turmas["7º A"]),
        ],
    }
    v["coord"].post("/api/rematricula", json=corpo)
    antes = v["prof"].get(f"/api/alunos/{a.alunos['joao'].id}")
    assert antes.status_code == 200  # com o 2027 só planejado, o 2026 segue sendo o ano atual
    r = v["admin"].post(f"/api/anos-letivos/{v['ano26']}/encerrar", json={"abrir_ano_id": ano27})
    assert r.json() == {"ano": 2026, "aberto": False, "ano_atual": 2027}
    # ano de 2027 aberto: o professor (copiado no 8º A) vê o João, mas não a Maria, que repete o 7º A sem ele
    assert v["prof"].get(f"/api/alunos/{a.alunos['joao'].id}").status_code == 200
    assert v["prof"].get(f"/api/alunos/{a.alunos['maria'].id}").status_code == 404
    assert v["prof"].get(f"/api/alunos/{a.alunos['pedro'].id}").status_code == 404


def test_linha_do_tempo_por_papel(virada, entrar):
    v, a = virada, virada["a"]
    ano27, turmas = _prepara(v)
    v["coord"].post(
        "/api/rematricula",
        json={
            "turma_origem_id": str(a.turma.id),
            "ano_destino_id": ano27,
            "itens": [
                _item(a.alunos["joao"], "aprovado", turmas["8º A"]),
                _item(a.alunos["maria"], "retido", turmas["7º A"]),
            ],
        },
    )
    t = v["coord"].get(f"/api/alunos/{a.alunos['joao'].id}/linha-do-tempo").json()
    assert [x["ano"] for x in t["anos"]] == [2026, 2027]
    d = t["anos"][0]
    assert (d["turma"], d["situacao"]) == ("7º A", "aprovado")
    assert d["disciplinas"][0]["disciplina"] == "Matemática" and float(d["disciplinas"][0]["media_anual"]) == 8.0
    assert t["anos"][1]["turma"] == "8º A" and t["anos"][1]["situacao"] == "cursando"
    # família: só o que foi publicado (a prova ainda não foi)
    mae = entrar("mae.a@teste.com").get(f"/api/alunos/{a.alunos['joao'].id}/linha-do-tempo").json()
    assert mae["so_publicadas"] is True and mae["anos"][0]["disciplinas"][0]["media_anual"] is None
    v["admin"].post(f"/api/avaliacoes/{v['av']}/publicar", json={"publicada": True})
    mae = entrar("mae.a@teste.com").get(f"/api/alunos/{a.alunos['joao'].id}/linha-do-tempo").json()
    assert float(mae["anos"][0]["disciplinas"][0]["media_anual"]) == 8.0
    # professor: só turma e resultado
    prof = v["prof"].get(f"/api/alunos/{a.alunos['joao'].id}/linha-do-tempo").json()
    assert prof["notas_visiveis"] is False and "disciplinas" not in prof["anos"][0]
    # outra escola e outro aluno
    assert entrar("mae.b@teste.com").get(f"/api/alunos/{a.alunos['joao'].id}/linha-do-tempo").status_code == 404
    assert entrar("mae.a@teste.com").get(f"/api/alunos/{a.alunos['maria'].id}/linha-do-tempo").status_code == 404
