from app import mail

CAB = "nome;sobrenome;data_nascimento;ra;turma;responsavel1_nome;responsavel1_tipo;responsavel1_email;responsavel1_telefone\n"


def _envia(c, csv: str | bytes, **form):
    data = csv.encode() if isinstance(csv, str) else csv
    return c.post(
        "/api/importacao/alunos",
        files={"arquivo": ("a.csv", data, "text/csv")},
        data={k: str(v).lower() for k, v in form.items()},
    )


def test_previa_mostra_erros_e_nao_grava(mundo, entrar):
    c = entrar("admin.a@teste.com")
    csv = CAB + (
        "Bia;Lima;10/02/2013;R1;7º A;Ana Lima;mae;ana@teste.com;11999\n"
        "Caio;;99/99/2013;R1;9º Z;Rui;tio;nao-e-email;\n"
        "Duda;Reis;2013-04-05;a-joao;8º B;;;;\n"
    )
    r = _envia(c, csv, confirmar=True).json()
    campos = {(e["linha"], e["campo"]) for e in r["erros"]}
    assert {
        (3, "sobrenome"),
        (3, "data_nascimento"),
        (3, "ra"),
        (3, "turma"),
        (3, "responsavel1_tipo"),
        (3, "responsavel1_email"),
        (4, "ra"),
    } <= campos
    assert r["importados"] == 0
    assert len(c.get("/api/alunos").json()) == 3  # nada gravado


def test_importa_com_convites_e_cp1252(mundo, entrar):
    c = entrar("admin.a@teste.com")
    csv = CAB + "Júlia;Araújo;10/02/2013;R9;7º A;Sônia Araújo;mae;sonia@teste.com;11999\nZé;Melo;01/01/2014;;8º b;;;;\n"
    previa = _envia(c, csv.encode("cp1252")).json()
    assert previa["erros"] == [] and len(previa["previa"]) == 2 and previa["importados"] == 0
    r = _envia(c, csv.encode("cp1252"), confirmar=True, enviar_convites=True).json()
    assert r["importados"] == 2 and r["convites"] == 1
    alunos = {x["nome"]: x for x in c.get("/api/alunos").json()}
    assert alunos["Júlia"]["turma"]["nome"] == "7º A" and alunos["Zé"]["turma"]["nome"] == "8º B"
    assert mail.outbox[-1]["To"] == "sonia@teste.com"


def test_colunas_obrigatorias(mundo, entrar):
    c = entrar("admin.a@teste.com")
    r = _envia(c, "nome,turma\nA,7º A\n")
    assert r.status_code == 422 and "sobrenome" in r.json()["detail"]


def test_modelo_csv(mundo, entrar):
    r = entrar("admin.a@teste.com").get("/api/importacao/modelo.csv")
    assert r.status_code == 200 and r.text.lstrip("﻿").startswith("nome;sobrenome")
