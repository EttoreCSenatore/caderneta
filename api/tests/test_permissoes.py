"""Matriz de permissões: o que cada perfil NÃO pode ver ou fazer."""

from sqlalchemy import text


def _nomes(resp):
    return {x["nome"] for x in resp.json()}


def test_professor_ve_so_alunos_das_suas_turmas(mundo, entrar):
    a, _ = mundo
    c = entrar("prof.a@teste.com")
    assert _nomes(c.get("/api/alunos")) == {"João", "Maria"}
    assert c.get(f"/api/alunos/{a.alunos['pedro'].id}").status_code == 404
    assert [t["nome"] for t in c.get("/api/turmas").json()] == ["7º A"]
    assert c.get(f"/api/turmas/{a.turma2.id}").status_code == 404


def test_professor_sem_atribuicao_nao_ve_alunos(mundo, entrar):
    c = entrar("prof2.a@teste.com")
    assert c.get("/api/alunos").json() == []
    assert c.get("/api/turmas").json() == []


def test_professor_nao_cadastra(mundo, entrar):
    a, _ = mundo
    c = entrar("prof.a@teste.com")
    novo = {"nome": "X", "sobrenome": "Y", "data_nascimento": "2013-01-01"}
    assert c.post("/api/alunos", json=novo).status_code == 403
    assert c.patch(f"/api/alunos/{a.alunos['joao'].id}", json={"nome": "Z"}).status_code == 403
    assert c.post("/api/convites", json={"email": "x@y.com", "nome": "Xx", "papel": "admin"}).status_code == 403
    assert c.get("/api/equipe").status_code == 403


def test_responsavel_ve_so_o_filho_e_nao_ve_restrito(mundo, entrar):
    a, _ = mundo
    c = entrar("mae.a@teste.com")
    assert _nomes(c.get("/api/alunos")) == {"João"}
    assert c.get(f"/api/alunos/{a.alunos['maria'].id}").status_code == 404
    det = c.get(f"/api/alunos/{a.alunos['joao'].id}").json()
    assert [r["nome"] for r in det["responsaveis"]] == ["Mãe do João"]
    assert "cpf" not in det
    turma = c.get(f"/api/turmas/{a.turma.id}").json()
    assert [x["nome"] for x in turma["alunos"]] == ["João"]  # não vê a lista da turma


def test_responsavel_edita_so_o_proprio_contato(mundo, entrar):
    a, _ = mundo
    c = entrar("mae.a@teste.com")
    r = c.patch(f"/api/responsaveis/{a.vinculos['mae'].id}", json={"telefone": "(11) 90000-0000", "restrito": False})
    assert r.status_code == 200 and r.json()["telefone"] == "(11) 90000-0000"
    assert c.patch(f"/api/responsaveis/{a.vinculos['pai'].id}", json={"telefone": "1"}).status_code == 404


def test_aluno_ve_so_a_si(mundo, entrar):
    a, _ = mundo
    c = entrar("aluno.a@teste.com")
    assert _nomes(c.get("/api/alunos")) == {"João"}
    assert "responsaveis" not in c.get(f"/api/alunos/{a.alunos['joao'].id}").json()
    assert c.get(f"/api/alunos/{a.alunos['joao'].id}/saude").status_code == 403


def test_saude_criptografada_e_por_perfil(mundo, entrar, owner_engine):
    a, _ = mundo
    joao = a.alunos["joao"].id
    adm = entrar("admin.a@teste.com")
    ficha = {
        "alergias": "Amendoim (grave)",
        "medicamentos": "Adrenalina autoinjetável",
        "alerta": "Alergia grave a amendoim",
    }
    assert adm.put(f"/api/alunos/{joao}/saude", json=ficha).status_code == 200

    with owner_engine.begin() as db:
        bruto = db.execute(text("SELECT dados_enc, alerta_enc FROM ficha_saude WHERE aluno_id=:a"), {"a": joao}).one()
    assert b"Amendoim" not in bruto[0] and b"amendoim" not in bruto[1]

    prof = entrar("prof.a@teste.com")
    assert prof.get(f"/api/alunos/{joao}/saude").json() == {"alerta": "Alergia grave a amendoim"}
    assert prof.get(f"/api/turmas/{a.turma.id}/alertas-saude").json()[0]["alerta"] == "Alergia grave a amendoim"
    assert prof.put(f"/api/alunos/{joao}/saude", json=ficha).status_code == 403

    mae = entrar("mae.a@teste.com")
    assert mae.get(f"/api/alunos/{joao}/saude").json()["alergias"] == "Amendoim (grave)"
    # O responsável atualiza a ficha, mas o alerta para professores continua sendo o da escola.
    assert mae.put(f"/api/alunos/{joao}/saude", json={**ficha, "alerta": "outro"}).status_code == 200
    assert prof.get(f"/api/alunos/{joao}/saude").json()["alerta"] == "Alergia grave a amendoim"

    with owner_engine.begin() as db:
        leituras = db.execute(text("SELECT count(*) FROM auditoria WHERE acao='saude_lida'")).scalar()
    assert leituras == 1  # leitura completa da mãe; a do professor (só alerta) não conta


def test_coordenacao_ve_mas_nao_edita(mundo, entrar):
    a, _ = mundo
    c = entrar("coord.a@teste.com")
    assert len(c.get("/api/alunos").json()) == 3
    assert c.patch(f"/api/alunos/{a.alunos['joao'].id}", json={"nome": "Z"}).status_code == 403
    assert c.get("/api/convites").status_code == 200


def test_busca_por_nome_completo(mundo, entrar):
    c = entrar("admin.a@teste.com")
    assert _nomes(c.get("/api/alunos", params={"q": "joão  silva"})) == {"João"}
    assert _nomes(c.get("/api/alunos", params={"q": "a-maria"})) == {"Maria"}  # RA
    assert c.get("/api/alunos", params={"q": "%"}).json() == []  # % não é curinga
