"""Sessão de desligados: aviso antes, adiamento, apagamento dos dados complementares e anonimização de contas."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import mail
from app.config import get_settings
from app.desligados import processa_desligados
from tests.conftest import Cliente

PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


def _n(owner_engine, sql, **p):
    with owner_engine.begin() as db:
        return db.execute(text(sql), p).scalar()


def _rodar(owner_engine, quando=None):
    with Session(owner_engine) as db, db.begin():
        return processa_desligados(db, quando or datetime.now(UTC))


def _envelhece(owner_engine, tabela, dias, onde="true"):
    with owner_engine.begin() as db:
        db.execute(text(f"UPDATE {tabela} SET desligado_em = now() - interval '{dias} days' WHERE {onde}"))


@pytest.fixture
def cheio(mundo, entrar, owner_engine):
    """João com dados complementares em todas as tabelas que o apagamento alcança."""
    a, _ = mundo
    joao = a.alunos["joao"]
    admin, prof, mae, coord = (
        entrar(x) for x in ("admin.a@teste.com", "prof.a@teste.com", "mae.a@teste.com", "coord.a@teste.com")
    )
    admin.patch(f"/api/alunos/{joao.id}", json={"cpf": "123.456.789-09"})
    assert (
        admin.put(f"/api/alunos/{joao.id}/saude", json={"alergias": "amendoim", "alerta": "alergia"}).status_code == 200
    )
    assert (
        prof.post(f"/api/alunos/{joao.id}/anotacoes", json={"tipo": "pedagogica", "corpo": "nota interna"}).status_code
        == 201
    )
    cid = prof.post("/api/conversas", json={"aluno_id": str(joao.id), "assunto": "x", "corpo": "oi"}).json()["id"]
    r = mae.post(
        f"/api/conversas/{cid}/mensagens-anexos", data={"corpo": "atestado"}, files=[("arquivos", ("a.pdf", PDF, "x"))]
    )
    assert r.status_code == 201, r.text
    prof.post("/api/autorizacoes", json={"titulo": "Passeio", "descricao": "x", "turma_id": str(a.turma.id)})
    item = mae.get("/api/autorizacoes").json()[0]
    assert (
        mae.put(
            f"/api/autorizacoes/{item['id']}/alunos/{item['aluno_id']}", json={"autoriza": True, "observacao": "ok"}
        ).status_code
        == 200
    )
    with owner_engine.begin() as db:
        atrib = str(db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar())
    d = prof.get(f"/api/atribuicoes/{atrib}/diario").json()
    mat = next(x["matricula_id"] for x in d["alunos"] if x["nome"].startswith("João"))
    reg = {"matricula_id": mat, "status": "justificada", "justificativa": "consulta com o cardiologista"}
    assert (
        prof.post(
            f"/api/atribuicoes/{atrib}/aulas", json={"data": "2026-03-10", "quantidade": 1, "registros": [reg]}
        ).status_code
        == 201
    )
    mail.outbox.clear()
    return {"a": a, "joao": joao, "admin": admin, "prof": prof, "mae": mae, "coord": coord, "atrib": atrib}


def _desliga(c, joao, situacao="transferido"):
    r = c["admin"].patch(f"/api/alunos/{joao.id}", json={"situacao": situacao})
    assert r.status_code == 200, r.text


def test_desligar_inicia_a_contagem_e_reativar_cancela(cheio, owner_engine):
    c = cheio
    _desliga(c, c["joao"])
    lista = c["coord"].get("/api/desligados").json()
    (item,) = lista["alunos"]
    assert item["status"] == "aguardando" and item["situacao"] == "transferido" and 364 <= item["dias_restantes"] <= 365
    assert lista["config"] == {"retencao_aluno_dias": 365, "retencao_usuario_dias": 180, "aviso_dias": 30}
    c["admin"].patch(f"/api/alunos/{c['joao'].id}", json={"situacao": "ativo"})
    assert c["coord"].get("/api/desligados").json()["alunos"] == []
    assert _n(owner_engine, "SELECT desligado_em FROM aluno WHERE ra = 'a-joao'") is None
    _desliga(c, c["joao"], "arquivado")
    _desliga(c, c["joao"], "concluiu")  # trocar de situação desligada não reinicia a contagem
    antes = c["coord"].get("/api/desligados").json()["alunos"][0]["dias_restantes"]
    assert antes in (364, 365)


def test_avisa_depois_apaga_so_o_complementar(cheio, owner_engine, entrar):
    c, joao = cheio, cheio["joao"]
    _desliga(c, joao)
    _envelhece(owner_engine, "aluno", 340, "ra = 'a-joao'")  # faltam 25 dias: já dentro da janela de aviso
    r = _rodar(owner_engine)
    assert r["avisos_alunos"] == 1 and "alunos_purgados" not in r
    notas = [n["titulo"] for n in c["admin"].get("/api/notificacoes").json()]
    assert "Dados de desligados serão apagados em breve" in notas
    assert [m["To"] for m in mail.outbox] == ["mae.a@teste.com"]  # o pai restrito não tem e-mail; a mãe sim
    corpo = mail.outbox[0].get_content()
    assert "João" not in corpo and "Escola A" in corpo and "30 dias" in corpo
    item = c["coord"].get("/api/desligados").json()["alunos"][0]
    assert item["status"] == "avisado"
    assert "alunos_purgados" not in _rodar(owner_engine)  # ainda não passaram os 30 dias de aviso
    assert _n(owner_engine, "SELECT count(*) FROM ficha_saude") == 1
    assert "alunos_purgados" not in _rodar(owner_engine, datetime.now(UTC) + timedelta(days=10))  # vence em 25 dias
    bins_antes = len(list(Path(get_settings().storage_dir).rglob("*.bin")))
    r = _rodar(owner_engine, datetime.now(UTC) + timedelta(days=31))
    assert r["alunos_purgados"] == 1
    # saiu o complementar
    for tabela in (
        "ficha_saude",
        "anotacao",
        "anotacao_versao",
        "conversa",
        "mensagem",
        "mensagem_anexo",
        "autorizacao_resposta",
    ):
        assert _n(owner_engine, f"SELECT count(*) FROM {tabela}") == 0, tabela
    assert (
        _n(
            owner_engine,
            "SELECT count(*) FROM vinculo_responsavel WHERE aluno_id = (SELECT id FROM aluno WHERE ra = 'a-joao')",
        )
        == 0
    )
    assert _n(owner_engine, "SELECT cpf FROM aluno WHERE ra = 'a-joao'") is None
    assert _n(owner_engine, "SELECT count(*) FROM frequencia WHERE justificativa IS NOT NULL") == 0
    assert _n(owner_engine, "SELECT count(*) FROM frequencia WHERE status = 'justificada'") == 1  # o status fica
    assert len(list(Path(get_settings().storage_dir).rglob("*.bin"))) == bins_antes - 1  # o anexo foi apagado do disco
    # ficou o núcleo histórico
    assert _n(owner_engine, "SELECT count(*) FROM aluno WHERE ra = 'a-joao' AND purgado_em IS NOT NULL") == 1
    assert (
        _n(owner_engine, "SELECT count(*) FROM matricula m JOIN aluno a ON a.id = m.aluno_id WHERE a.ra = 'a-joao'")
        == 1
    )
    pdf = c["admin"].post(f"/api/alunos/{joao.id}/historico-escolar")
    assert pdf.status_code == 200 and "João Silva A".encode("cp1252") in pdf.content
    assert c["coord"].get("/api/desligados").json()["alunos"][0]["status"] == "concluido"
    # a mãe e a conta do aluno ficaram sem vínculo: perdem o acesso e entram na contagem de usuários desligados
    desligados = {u["papel"] for u in c["coord"].get("/api/desligados").json()["usuarios"]}
    assert desligados == {"responsavel", "aluno"}
    assert _n(owner_engine, "SELECT count(*) FROM auditoria WHERE acao = 'desligados.purgar_aluno'") == 1
    assert _rodar(owner_engine, datetime.now(UTC) + timedelta(days=32)).get("alunos_purgados") is None  # idempotente


def test_adiar_cria_novo_prazo_e_novo_aviso(cheio, owner_engine):
    c, joao = cheio, cheio["joao"]
    _desliga(c, joao)
    _envelhece(owner_engine, "aluno", 340, "ra = 'a-joao'")
    _rodar(owner_engine)
    assert c["coord"].post(f"/api/desligados/alunos/{joao.id}/adiar", json={"dias": 90}).status_code == 403
    assert (
        c["admin"].post(f"/api/desligados/alunos/{joao.id}/adiar", json={"dias": 7}).status_code == 409
    )  # já é depois
    r = c["admin"].post(f"/api/desligados/alunos/{joao.id}/adiar", json={"dias": 90})
    assert r.status_code == 200
    item = c["coord"].get("/api/desligados").json()["alunos"][0]
    assert item["adiado"] is True and item["status"] == "aguardando" and 89 <= item["dias_restantes"] <= 90
    assert "alunos_purgados" not in _rodar(owner_engine, datetime.now(UTC) + timedelta(days=40))
    r = _rodar(owner_engine, datetime.now(UTC) + timedelta(days=65))  # entrou na janela do novo prazo: novo aviso
    assert r["avisos_alunos"] == 1
    assert _n(owner_engine, "SELECT count(*) FROM auditoria WHERE acao = 'desligados.adiar_aluno'") == 1
    assert (
        c["admin"].post(f"/api/desligados/alunos/{c['a'].alunos['pedro'].id}/adiar", json={"dias": 30}).status_code
        == 404
    )


def test_apagar_agora_exige_confirmacao(cheio, owner_engine):
    c, joao = cheio, cheio["joao"]
    url = f"/api/desligados/alunos/{joao.id}/apagar-agora"
    assert c["admin"].post(url, json={"confirmacao": "APAGAR"}).status_code == 404  # ainda ativo
    _desliga(c, joao)
    assert c["coord"].post(url, json={"confirmacao": "APAGAR"}).status_code == 403
    assert c["admin"].post(url, json={"confirmacao": "apagar"}).status_code == 422
    r = c["admin"].post(url, json={"confirmacao": "APAGAR"})
    assert r.status_code == 200 and r.json()["ficha_saude"] == 1 and r.json()["anotacoes"] == 1
    assert _n(owner_engine, "SELECT count(*) FROM ficha_saude") == 0
    assert c["admin"].post(url, json={"confirmacao": "APAGAR"}).status_code == 409


def test_configuracao_dos_prazos(cheio):
    c = cheio
    ok = {"retencao_aluno_dias": 100, "retencao_usuario_dias": 60, "aviso_dias": 15}
    assert c["coord"].put("/api/desligados/config", json=ok).status_code == 403
    assert c["admin"].put("/api/desligados/config", json={**ok, "aviso_dias": 60}).status_code == 422  # aviso >= prazo
    assert c["admin"].put("/api/desligados/config", json={**ok, "retencao_aluno_dias": 10}).status_code == 422
    assert c["admin"].put("/api/desligados/config", json=ok).status_code == 200
    _desliga(c, c["joao"])
    lista = c["coord"].get("/api/desligados").json()
    assert lista["config"]["aviso_dias"] == 15 and 99 <= lista["alunos"][0]["dias_restantes"] <= 100


def test_funcionario_desligado_e_anonimizado(cheio, owner_engine, entrar):
    c = cheio
    pid = _n(
        owner_engine,
        "SELECT p.id FROM usuario_perfil p JOIN usuario u ON u.id = p.usuario_id WHERE u.email = 'prof.a@teste.com'",
    )
    assert c["admin"].patch(f"/api/equipe/{pid}", json={"ativo": False}).status_code == 200
    (u,) = [x for x in c["coord"].get("/api/desligados").json()["usuarios"] if x["papel"] == "professor"]
    assert u["nome"] == "Prof.A" and u["status"] == "aguardando" and 179 <= u["dias_restantes"] <= 180
    _envelhece(owner_engine, "usuario_perfil", 170, "NOT ativo")
    r = _rodar(owner_engine)
    assert r["avisos_usuarios"] == 1
    assert [m["To"] for m in mail.outbox] == ["prof.a@teste.com"] and "anonimizados" in mail.outbox[0].get_content()
    assert "usuarios_anonimizados" not in _rodar(owner_engine, datetime.now(UTC) + timedelta(days=5))
    assert _rodar(owner_engine, datetime.now(UTC) + timedelta(days=31))["usuarios_anonimizados"] == 1
    with owner_engine.begin() as db:
        usu = db.execute(
            text(
                "SELECT nome, email, senha_hash, ativo, anonimizado_em FROM usuario WHERE id = (SELECT usuario_id FROM usuario_perfil WHERE id = :p)"
            ),
            {"p": pid},
        ).one()
        assert (usu.nome, usu.senha_hash, usu.ativo) == ("Ex-usuário", None, False)
        assert usu.email.endswith("@anonimo.invalid") and usu.anonimizado_em is not None
        assert (
            db.execute(
                text(
                    "SELECT count(*) FROM sessao WHERE usuario_id = (SELECT usuario_id FROM usuario_perfil WHERE id = :p)"
                ),
                {"p": pid},
            ).scalar()
            == 0
        )
    # o que ele escreveu continua, agora atribuído a "Ex-usuário"
    anot = c["coord"].get(f"/api/alunos/{c['joao'].id}/anotacoes").json()
    assert anot[0]["autor"] == "Ex-usuário"
    assert Cliente().post(
        "/api/auth/login", json={"email": "prof.a@teste.com", "senha": "senha-de-teste-123"}
    ).status_code in (401, 403, 422)
    assert c["coord"].get("/api/desligados").json()["usuarios"][0]["nome"] == "Ex-usuário"


def test_conta_com_acesso_em_outra_escola_nao_e_anonimizada(cheio, owner_engine, mundo):
    c, (a, b) = cheio, mundo
    with owner_engine.begin() as db:
        uid = db.execute(text("SELECT id FROM usuario WHERE email = 'prof.a@teste.com'")).scalar()
        db.execute(
            text(
                "INSERT INTO usuario_perfil (id, usuario_id, escola_id, papel, ativo, criado_em) VALUES (gen_random_uuid(), :u, :e, 'professor', true, now())"
            ),
            {"u": uid, "e": b.escola.id},
        )
        pid = db.execute(
            text("SELECT id FROM usuario_perfil WHERE usuario_id = :u AND escola_id = :e"), {"u": uid, "e": a.escola.id}
        ).scalar()
    c["admin"].patch(f"/api/equipe/{pid}", json={"ativo": False})
    _envelhece(owner_engine, "usuario_perfil", 200, "NOT ativo")
    _rodar(owner_engine)
    r = _rodar(owner_engine, datetime.now(UTC) + timedelta(days=31))
    assert "usuarios_anonimizados" not in r
    assert _n(owner_engine, "SELECT anonimizado_em FROM usuario WHERE id = :u", u=uid) is None


def test_isolamento_entre_escolas(cheio, entrar):
    c = cheio
    _desliga(c, c["joao"])
    b_admin = entrar("admin.b@teste.com")
    assert b_admin.get("/api/desligados").json()["alunos"] == []
    assert (
        b_admin.post(f"/api/desligados/alunos/{c['joao'].id}/apagar-agora", json={"confirmacao": "APAGAR"}).status_code
        == 404
    )
    assert entrar("prof.a@teste.com").get("/api/desligados").status_code == 403
    assert entrar("mae.a@teste.com").get("/api/desligados").status_code == 403
