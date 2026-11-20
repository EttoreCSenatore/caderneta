"""M2: diário (avaliações, notas, chamada), boletim, regra de média e fechamento de período."""

from datetime import date, timedelta

import pytest
from sqlalchemy import text


@pytest.fixture
def diario(mundo, entrar, owner_engine):
    a, b = mundo
    with owner_engine.begin() as db:
        atrib = db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar()
    prof = entrar("prof.a@teste.com")
    d = prof.get(f"/api/atribuicoes/{atrib}/diario").json()
    mat = {x["nome"].split()[0]: x["matricula_id"] for x in d["alunos"]}
    return {"a": a, "b": b, "atrib": str(atrib), "prof": prof, "periodo": d["periodos"][0]["id"], "mat": mat}


def _avaliacao(c, ctx, **kw):
    body = {"periodo_id": ctx["periodo"], "nome": "Prova 1", "peso": 2, **kw}
    r = c.post(f"/api/atribuicoes/{ctx['atrib']}/avaliacoes", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_lancamento_e_media(diario):
    c, m = diario["prof"], diario["mat"]
    p1 = _avaliacao(c, diario, nome="Prova 1", peso=2)
    tr = _avaliacao(c, diario, nome="Trabalho", peso=1, tipo="trabalho")
    assert (
        c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 7}]}).status_code
        == 200
    )
    r = c.put(f"/api/avaliacoes/{tr}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 10}]}).json()
    assert r["medias"][m["João"]]["media"] == 8.0  # (7*2 + 10) / 3
    d = c.get(f"/api/atribuicoes/{diario['atrib']}/diario").json()
    assert d["notas"][p1][m["João"]]["valor"] == 7.0
    assert d["medias"][m["Maria"]]["pendentes"] == 2
    # validações
    assert (
        c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 11}]}).status_code
        == 422
    )
    pedro = diario["a"].alunos["pedro"].id  # outra turma: usa o id do aluno como matrícula falsa
    assert (
        c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": str(pedro), "valor": 5}]}).status_code
        == 422
    )
    fora = {"periodo_id": diario["periodo"], "nome": "X", "data": "2026-10-01"}
    assert c.post(f"/api/atribuicoes/{diario['atrib']}/avaliacoes", json=fora).status_code == 422


def test_recuperacao_substitui(diario):
    c, m = diario["prof"], diario["mat"]
    p1 = _avaliacao(c, diario)
    rec = _avaliacao(c, diario, nome="Recuperação", tipo="recuperacao")
    c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 4}]})
    r = c.put(f"/api/avaliacoes/{rec}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 6.5}]}).json()
    assert r["medias"][m["João"]]["media"] == 6.5 and r["medias"][m["João"]]["recuperacao_aplicada"]


def test_quem_pode_ver_e_editar_o_diario(diario, entrar, owner_engine):
    atrib, m = diario["atrib"], diario["mat"]
    p1 = _avaliacao(diario["prof"], diario)
    nota = {"notas": [{"matricula_id": m["João"], "valor": 9}]}
    assert entrar("prof2.a@teste.com").get(f"/api/atribuicoes/{atrib}/diario").status_code == 404
    assert entrar("admin.b@teste.com").get(f"/api/atribuicoes/{atrib}/diario").status_code == 404
    for quem in ("mae.a@teste.com", "aluno.a@teste.com"):
        assert entrar(quem).get(f"/api/atribuicoes/{atrib}/diario").status_code == 403
    coord = entrar("coord.a@teste.com")
    assert coord.get(f"/api/atribuicoes/{atrib}/diario").status_code == 200
    assert coord.put(f"/api/avaliacoes/{p1}/notas", json=nota).status_code == 403
    adm = entrar("admin.a@teste.com")
    assert adm.put(f"/api/avaliacoes/{p1}/notas", json=nota).status_code == 422  # sem justificativa
    r = adm.put(f"/api/avaliacoes/{p1}/notas", json={**nota, "justificativa": "Erro de digitação"})
    assert r.status_code == 200
    with owner_engine.begin() as db:
        det = db.execute(text("SELECT detalhes FROM auditoria WHERE acao = 'notas_corrigidas'")).scalar()
    assert det["justificativa"] == "Erro de digitação" and det["mudancas"][0]["depois"] == "9.00"


def test_fechamento_trava_professor(diario, entrar):
    c, m, per = diario["prof"], diario["mat"], diario["periodo"]
    p1 = _avaliacao(c, diario)
    coord = entrar("coord.a@teste.com")
    assert coord.post(f"/api/periodos/{per}/fechamento", json={"fechado": True}).json()["fechado"] is True
    nota = {"notas": [{"matricula_id": m["João"], "valor": 5}]}
    assert c.put(f"/api/avaliacoes/{p1}/notas", json=nota).status_code == 409
    assert c.post(f"/api/avaliacoes/{p1}/publicar", json={"publicada": True}).status_code == 409
    assert c.get(f"/api/atribuicoes/{diario['atrib']}/diario").json()["pode_editar"] is False
    assert coord.post(f"/api/periodos/{per}/fechamento", json={"fechado": False}).status_code == 403
    adm = entrar("admin.a@teste.com")
    assert adm.put(f"/api/avaliacoes/{p1}/notas", json={**nota, "justificativa": "Revisão de prova"}).status_code == 200
    assert adm.post(f"/api/periodos/{per}/fechamento", json={"fechado": False}).status_code == 200
    assert c.put(f"/api/avaliacoes/{p1}/notas", json=nota).status_code == 200


def test_boletim_familia_ve_so_publicadas(diario, entrar):
    c, m, a = diario["prof"], diario["mat"], diario["a"]
    p1 = _avaliacao(c, diario)
    c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 8.5}]})
    joao = a.alunos["joao"].id
    mae = entrar("mae.a@teste.com")
    b = mae.get(f"/api/alunos/{joao}/boletim").json()
    assert b["somente_publicadas"] and b["disciplinas"][0]["periodos"][0]["avaliacoes"] == []
    assert b["disciplinas"][0]["periodos"][0]["media"] is None
    assert c.post(f"/api/avaliacoes/{p1}/publicar", json={"publicada": True}).status_code == 200
    b = mae.get(f"/api/alunos/{joao}/boletim").json()
    linha = b["disciplinas"][0]
    assert linha["disciplina"] == "Matemática" and linha["periodos"][0]["media"] == 8.5
    assert linha["situacao"] == "cursando"  # período ainda aberto: sem situação final
    entrar("coord.a@teste.com").post(f"/api/periodos/{diario['periodo']}/fechamento", json={"fechado": True})
    linha = mae.get(f"/api/alunos/{joao}/boletim").json()["disciplinas"][0]
    assert linha["situacao"] == "aprovado"
    # o próprio aluno vê o boletim; ninguém da família vê o de outro aluno
    assert entrar("aluno.a@teste.com").get(f"/api/alunos/{joao}/boletim").status_code == 200
    assert mae.get(f"/api/alunos/{a.alunos['maria'].id}/boletim").status_code == 404
    assert entrar("prof2.a@teste.com").get(f"/api/alunos/{joao}/boletim").status_code == 404


def test_chamada_e_frequencia(diario, entrar):
    c, m, a = diario["prof"], diario["mat"], diario["a"]
    base = {"data": "2026-03-10", "quantidade": 2}
    r = c.post(
        f"/api/atribuicoes/{diario['atrib']}/aulas",
        json={**base, "registros": [{"matricula_id": m["João"], "status": "falta"}]},
    )
    assert r.status_code == 201
    aula = r.json()["id"]
    c.post(f"/api/atribuicoes/{diario['atrib']}/aulas", json={"data": "2026-03-11", "quantidade": 2, "registros": []})
    d = c.get(f"/api/atribuicoes/{diario['atrib']}/diario").json()
    joao = next(x for x in d["alunos"] if x["matricula_id"] == m["João"])
    assert d["aulas_dadas"] == 4 and joao["faltas"] == 2 and joao["frequencia"] == 50.0
    # justificar não devolve a presença (LDB), mas fica registrado
    c.put(
        f"/api/aulas/{aula}",
        json={
            **base,
            "registros": [{"matricula_id": m["João"], "status": "justificada", "justificativa": "Atestado médico"}],
        },
    )
    b = entrar("admin.a@teste.com").get(f"/api/alunos/{a.alunos['joao'].id}/boletim").json()
    assert b["disciplinas"][0]["faltas"] == 2 and b["disciplinas"][0]["faltas_justificadas"] == 2
    # marcar presente apaga o registro
    c.put(f"/api/aulas/{aula}", json={**base, "registros": [{"matricula_id": m["João"], "status": "presente"}]})
    assert (
        c.get(f"/api/atribuicoes/{diario['atrib']}/aulas?periodo_id={diario['periodo']}").json()[1]["registros"] == []
    )
    amanha = (date.today() + timedelta(days=1)).isoformat()
    assert c.post(f"/api/atribuicoes/{diario['atrib']}/aulas", json={"data": amanha}).status_code == 422
    assert c.post(f"/api/atribuicoes/{diario['atrib']}/aulas", json={"data": "2025-06-01"}).status_code == 422


def test_regra_de_media(diario, entrar):
    c, m = diario["prof"], diario["mat"]
    p1 = _avaliacao(c, diario, peso=3)
    tr = _avaliacao(c, diario, nome="T", peso=1)
    c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 5}]})
    c.put(f"/api/avaliacoes/{tr}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 9}]})
    assert c.get(f"/api/atribuicoes/{diario['atrib']}/diario").json()["medias"][m["João"]]["media"] == 6.0
    regra = {
        "tipo_media": "aritmetica",
        "recuperacao": "nenhuma",
        "arredondamento": "meio",
        "nota_maxima": 10,
        "media_aprovacao": 7,
        "frequencia_minima": 75,
    }
    assert entrar("coord.a@teste.com").put("/api/regra-media", json=regra).status_code == 403
    adm = entrar("admin.a@teste.com")
    assert adm.put("/api/regra-media", json={**regra, "pesos_periodos": [1, 2]}).status_code == 422
    assert adm.put("/api/regra-media", json=regra).status_code == 200
    assert c.get(f"/api/atribuicoes/{diario['atrib']}/diario").json()["medias"][m["João"]]["media"] == 7.0
    assert entrar("mae.a@teste.com").get("/api/regra-media").json()["media_aprovacao"] == 7.0


def test_pendencias(diario, entrar):
    c, m = diario["prof"], diario["mat"]
    p1 = _avaliacao(c, diario)
    c.put(f"/api/avaliacoes/{p1}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 5}]})
    pend = entrar("coord.a@teste.com").get(f"/api/periodos/{diario['periodo']}/pendencias").json()
    mat = next(x for x in pend if x["turma"] == "7º A")
    assert mat["avaliacoes"] == 1 and mat["notas_em_branco"] == 1 and mat["nao_publicadas"] == 1
    assert c.get(f"/api/periodos/{diario['periodo']}/pendencias").status_code == 403


def test_toda_tabela_escolar_tem_rls(owner_engine):
    """Regra do ADR 0002: tabela nova sem RLS quebra o CI."""
    with owner_engine.begin() as db:
        sem = (
            db.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND NOT rowsecurity "
                    "AND tablename NOT IN ('alembic_version', 'sessao', 'token_senha', 'limite_taxa', 'registro_operacao')"
                )
            )
            .scalars()
            .all()
        )
    assert sem == []
