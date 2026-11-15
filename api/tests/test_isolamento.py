"""Uma escola nunca vê dados de outra: pela API e direto no banco (RLS)."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.config import get_settings


def test_admin_nao_ve_outra_escola_pela_api(mundo, entrar):
    a, b = mundo
    c = entrar("admin.a@teste.com")
    nomes = {x["sobrenome"] for x in c.get("/api/alunos").json()}
    assert nomes == {"Silva A"}
    aluno_b = b.alunos["joao"].id
    assert c.get(f"/api/alunos/{aluno_b}").status_code == 404
    assert c.patch(f"/api/alunos/{aluno_b}", json={"nome": "Hack"}).status_code == 404
    assert c.get(f"/api/alunos/{aluno_b}/saude").status_code == 404
    assert c.get(f"/api/turmas/{b.turma.id}").status_code == 404
    assert c.post(f"/api/alunos/{a.alunos['joao'].id}/matricula", json={}).status_code in (404, 405)
    assert c.put(f"/api/alunos/{a.alunos['joao'].id}/matricula", json={"turma_id": str(b.turma.id)}).status_code == 404
    equipe = {x["email"] for x in c.get("/api/equipe").json()}
    assert all(e.endswith(".a@teste.com") for e in equipe)


def test_nao_escolhe_perfil_de_outro_usuario(mundo, entrar, owner_engine):
    _, b = mundo
    with owner_engine.begin() as db:
        perfil_b = db.execute(
            text("SELECT id FROM usuario_perfil WHERE usuario_id = :u"), {"u": b.usuarios["admin"].id}
        ).scalar()
    c = entrar("admin.a@teste.com")
    assert c.post("/api/auth/perfil", json={"perfil_id": str(perfil_b)}).status_code == 404


@pytest.fixture
def app_conn(owner_engine):
    eng = create_engine(get_settings().database_url)
    with eng.connect() as conn:
        yield conn
    eng.dispose()


def test_rls_sem_contexto_nao_ve_nada(mundo, app_conn):
    with app_conn.begin():
        for t in ("aluno", "turma", "matricula", "vinculo_responsavel", "usuario", "usuario_perfil", "escola"):
            assert app_conn.execute(text(f"SELECT count(*) FROM {t}")).scalar() == 0, t


def test_rls_com_contexto_ve_so_a_escola(mundo, app_conn):
    a, b = mundo
    with app_conn.begin():
        app_conn.execute(text("SELECT set_config('app.escola_id', :e, true)"), {"e": str(a.escola.id)})
        escolas = {r[0] for r in app_conn.execute(text("SELECT DISTINCT escola_id FROM aluno"))}
        assert escolas == {a.escola.id}
        with pytest.raises(DBAPIError):  # não grava linha de outra escola
            app_conn.execute(
                text("INSERT INTO disciplina (id, escola_id, nome, ativo) VALUES (gen_random_uuid(), :e, 'X', true)"),
                {"e": str(b.escola.id)},
            )


def test_api_nao_altera_auditoria_nem_cria_escola(mundo, app_conn):
    a, _ = mundo
    with app_conn.begin():
        app_conn.execute(text("SELECT set_config('app.escola_id', :e, true)"), {"e": str(a.escola.id)})
        with pytest.raises(DBAPIError):
            app_conn.execute(text("UPDATE auditoria SET acao = 'x'"))
    with app_conn.begin(), pytest.raises(DBAPIError):
        app_conn.execute(
            text("INSERT INTO escola (id, nome, fuso, criado_em) VALUES (gen_random_uuid(), 'X', 'x', now())")
        )
