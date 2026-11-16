"""Direitos do titular (M8.2): exportação dos próprios dados, pedidos com prazo e atendimento pela direção."""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from tests.conftest import SENHA


def _exporta(c, senha=SENHA, **corpo):
    return c.post("/api/meus-dados/exportar", json={"senha": senha, **corpo})


def _auditoria(owner_engine, acao):
    with owner_engine.begin() as db:
        return db.execute(text("SELECT count(*) FROM auditoria WHERE acao = :a"), {"a": acao}).scalar()


def test_exportar_exige_a_senha_de_novo(mundo, entrar):
    c = entrar("mae.a@teste.com")
    assert _exporta(c, senha="errada-123").status_code == 400
    r = _exporta(c)
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    dados = r.json()
    assert dados["conta"]["email"] == "mae.a@teste.com"
    assert "como_os_dados_sao_tratados" in dados and dados["como_os_dados_sao_tratados"]["finalidades"]
    texto = json.dumps(dados)
    assert "senha_hash" not in texto and "totp" not in texto.replace("verificacao_em_duas_etapas", "")


def test_exportar_registra_auditoria(mundo, entrar, owner_engine):
    _exporta(entrar("mae.a@teste.com"))
    assert _auditoria(owner_engine, "titular.exportou") == 1


def test_responsavel_exporta_dados_do_filho_com_saude_e_sem_dados_de_terceiros(mundo, entrar):
    a, _ = mundo
    joao = a.alunos["joao"]
    mae = entrar("mae.a@teste.com")
    assert mae.put(
        f"/api/alunos/{joao.id}/saude", json={"alergias": "amendoim", "alerta": "Alergia grave a amendoim"}
    ).status_code in (200, 403)  # quem grava é a escola; o teste de leitura abaixo usa a ficha da secretaria
    entrar("admin.a@teste.com").put(f"/api/alunos/{joao.id}/saude", json={"alergias": "amendoim", "alerta": "Alergia"})
    dados = _exporta(mae, aluno_id=str(joao.id)).json()
    assert dados["aluno"]["nome"] == "João"
    assert dados["saude"]["alergias"] == "amendoim"
    # contatos de outros responsáveis ficam de fora; só o do próprio vínculo aparece completo
    outros = [r for r in dados["responsaveis"] if "telefone" not in r]
    assert all(set(r) == {"tipo", "nome"} for r in outros)


def test_conta_do_aluno_exporta_sem_ficha_de_saude(mundo, entrar):
    a, _ = mundo
    joao = a.alunos["joao"]
    entrar("admin.a@teste.com").put(f"/api/alunos/{joao.id}/saude", json={"alergias": "amendoim", "alerta": "Alergia"})
    dados = _exporta(entrar("aluno.a@teste.com"), aluno_id=str(joao.id)).json()
    assert "saude" not in dados


def test_exportacao_nao_vaza_anotacoes_internas_nem_de_outros_alunos(mundo, entrar):
    a, b = mundo
    joao = a.alunos["joao"]
    prof = entrar("prof.a@teste.com")
    for tipo, corpo in (
        ("pedagogica", "SEGREDO-PEDAGOGICO"),
        ("elogio", "PARABENS-VISIVEL"),
        ("reservada", "SEGREDO-RESERVADA"),
    ):
        r = prof.post(f"/api/alunos/{joao.id}/anotacoes", json={"tipo": tipo, "corpo": corpo})
        if r.status_code == 403:  # reservada é da equipe
            entrar("coord.a@teste.com").post(f"/api/alunos/{joao.id}/anotacoes", json={"tipo": tipo, "corpo": corpo})
    texto = json.dumps(_exporta(entrar("mae.a@teste.com"), aluno_id=str(joao.id)).json())
    assert "PARABENS-VISIVEL" in texto
    assert "SEGREDO-PEDAGOGICO" not in texto and "SEGREDO-RESERVADA" not in texto


def test_nao_exporta_aluno_de_outra_familia_nem_como_professor(mundo, entrar):
    a, b = mundo
    outro = b.alunos["joao"]
    assert _exporta(entrar("mae.a@teste.com"), aluno_id=str(outro.id)).status_code == 404
    assert _exporta(entrar("prof.a@teste.com"), aluno_id=str(a.alunos["joao"].id)).status_code == 403


# --- pedidos --------------------------------------------------------------------------------------------------


def test_pedido_tem_prazo_de_15_dias_e_a_direcao_e_avisada(mundo, entrar):
    mae = entrar("mae.a@teste.com")
    r = mae.post(
        "/api/meus-dados/pedidos", json={"tipo": "eliminacao", "descricao": "Quero apagar os dados do meu filho."}
    )
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["status"] == "aberto" and p["dias_restantes"] in (14, 15)
    assert len(mae.get("/api/meus-dados/pedidos").json()) == 1
    admin = entrar("admin.a@teste.com")
    lista = admin.get("/api/pedidos-titulares").json()
    assert len(lista) == 1 and lista[0]["solicitante"]["email"] == "mae.a@teste.com"
    assert admin.get("/api/pedidos-titulares/contagem").json() == {"abertos": 1, "vencidos": 0}
    notifs = admin.get("/api/notificacoes").json()
    assert any(n["tipo"] == "titular" for n in (notifs["itens"] if isinstance(notifs, dict) else notifs))


def test_so_a_equipe_ve_a_fila_e_so_a_direcao_responde(mundo, entrar):
    mae = entrar("mae.a@teste.com")
    pid = mae.post(
        "/api/meus-dados/pedidos", json={"tipo": "acesso", "descricao": "Quero uma cópia dos meus dados."}
    ).json()["id"]
    for quem in ("mae.a@teste.com", "prof.a@teste.com", "aluno.a@teste.com"):
        assert entrar(quem).get("/api/pedidos-titulares").status_code == 403
    corpo = {"status": "atendido", "resposta": "Enviamos o arquivo por e-mail."}
    assert entrar("coord.a@teste.com").post(f"/api/pedidos-titulares/{pid}/responder", json=corpo).status_code == 403
    assert entrar("admin.a@teste.com").post(f"/api/pedidos-titulares/{pid}/responder", json=corpo).status_code == 200


def test_resposta_notifica_o_titular_e_nao_pode_ser_refeita(mundo, entrar, owner_engine):
    mae = entrar("mae.a@teste.com")
    pid = mae.post(
        "/api/meus-dados/pedidos", json={"tipo": "correcao", "descricao": "O sobrenome do meu filho está errado."}
    ).json()["id"]
    admin = entrar("admin.a@teste.com")
    assert (
        admin.post(
            f"/api/pedidos-titulares/{pid}/responder", json={"status": "atendido", "resposta": "curta"}
        ).status_code
        == 422
    )
    r = admin.post(
        f"/api/pedidos-titulares/{pid}/responder",
        json={"status": "negado", "resposta": "Falta documento que comprove a mudança."},
    )
    assert r.status_code == 200 and r.json()["status"] == "negado"
    assert (
        admin.post(
            f"/api/pedidos-titulares/{pid}/responder",
            json={"status": "atendido", "resposta": "Já resolvido, obrigado."},
        ).status_code
        == 409
    )
    meu = mae.get("/api/meus-dados/pedidos").json()[0]
    assert meu["status"] == "negado" and "documento" in meu["resposta"]
    assert admin.get("/api/pedidos-titulares/contagem").json()["abertos"] == 0
    assert _auditoria(owner_engine, "titular.respondido") == 1


def test_pedido_por_outro_canal_conta_o_prazo_da_data_original(mundo, entrar):
    admin = entrar("admin.a@teste.com")
    recebido = (datetime.now(UTC) - timedelta(days=20)).date().isoformat()
    r = admin.post(
        "/api/pedidos-titulares",
        json={
            "tipo": "acesso",
            "canal": "presencial",
            "titular_nome": "Dona Maria",
            "titular_contato": "11 99999-0000",
            "descricao": "Pediu no balcão uma cópia dos dados do neto.",
            "recebido_em": recebido,
        },
    )
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["vencido"] is True and p["dias_restantes"] < 0
    assert admin.get("/api/pedidos-titulares/contagem").json() == {"abertos": 1, "vencidos": 1}
    futuro = (datetime.now(UTC) + timedelta(days=3)).date().isoformat()
    assert (
        admin.post(
            "/api/pedidos-titulares",
            json={
                "tipo": "acesso",
                "canal": "email",
                "titular_nome": "Fulano",
                "descricao": "Pedido com data futura inválida.",
                "recebido_em": futuro,
            },
        ).status_code
        == 422
    )
    assert (
        entrar("coord.a@teste.com")
        .post(
            "/api/pedidos-titulares",
            json={
                "tipo": "acesso",
                "canal": "email",
                "titular_nome": "Fulano",
                "descricao": "Coordenação não registra pedidos.",
            },
        )
        .status_code
        == 403
    )


def test_direcao_gera_o_arquivo_do_pedido_e_fica_auditado(mundo, entrar, owner_engine):
    a, _ = mundo
    mae = entrar("mae.a@teste.com")
    pid = mae.post(
        "/api/meus-dados/pedidos",
        json={
            "tipo": "portabilidade",
            "descricao": "Preciso levar os dados dele para a nova escola.",
            "aluno_id": str(a.alunos["joao"].id),
        },
    ).json()["id"]
    r = entrar("admin.a@teste.com").post(f"/api/pedidos-titulares/{pid}/exportar")
    assert r.status_code == 200 and r.json()["aluno"]["nome"] == "João"
    assert _auditoria(owner_engine, "titular.exportou_para_titular") == 1


def test_isolamento_entre_escolas_nos_pedidos(mundo, entrar):
    a, b = mundo
    entrar("mae.a@teste.com").post(
        "/api/meus-dados/pedidos", json={"tipo": "acesso", "descricao": "Quero meus dados, por favor."}
    )
    assert entrar("admin.b@teste.com").get("/api/pedidos-titulares").json() == []


def test_retencao_apaga_pedido_respondido_antigo_e_nunca_o_aberto(mundo, entrar, owner_engine):
    from sqlalchemy.orm import Session

    from app.retencao import elimina_vencidos

    mae, admin = entrar("mae.a@teste.com"), entrar("admin.a@teste.com")
    ids = [
        mae.post(
            "/api/meus-dados/pedidos", json={"tipo": "acesso", "descricao": f"Pedido numero {i} de teste."}
        ).json()["id"]
        for i in range(3)
    ]
    for pid in ids[:2]:
        assert (
            admin.post(
                f"/api/pedidos-titulares/{pid}/responder",
                json={"status": "atendido", "resposta": "Atendido por e-mail."},
            ).status_code
            == 200
        )
    with owner_engine.begin() as db:
        db.execute(
            text("UPDATE pedido_titular SET respondido_em = now() - interval '1900 days' WHERE id = :i"), {"i": ids[0]}
        )
        db.execute(
            text("UPDATE pedido_titular SET recebido_em = now() - interval '900 days' WHERE id = :i"), {"i": ids[2]}
        )
    with Session(owner_engine) as db, db.begin():
        assert elimina_vencidos(db)["pedidos_titular"] == 1
    restantes = {p["id"] for p in admin.get("/api/pedidos-titulares").json()}
    assert restantes == {ids[1], ids[2]}  # o respondido há pouco e o ainda aberto (mesmo antigo) continuam
