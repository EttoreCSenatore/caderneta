"""MO.6: apagar só a demonstração e simular a atividade da semana, sem nunca tocar uma escola real."""

from datetime import timedelta

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import seed
from app.config import get_settings
from app.models import AnoLetivo, Aula, Avaliacao, Aviso, Escola, Papel, Periodo, Usuario, UsuarioPerfil


def _conta(owner_engine, modelo, *filtros) -> int:
    with Session(owner_engine) as db:
        return db.scalar(select(func.count()).select_from(modelo).where(*filtros))


@pytest.fixture
def demo(owner_engine):
    seed.seed()
    with Session(owner_engine) as db:
        return db.scalars(select(Escola).where(Escola.nome == seed.NOME_ESCOLA)).one().id


def test_remover_apaga_so_a_demonstracao(mundo, demo, owner_engine):
    reais = _conta(owner_engine, Escola, Escola.id != demo)
    contas_reais = _conta(owner_engine, Usuario, ~Usuario.email.like(f"%{seed.DOMINIO_DEMO}"))
    assert reais == 2 and contas_reais > 0
    r = seed.remover()
    assert r["escolas"] == 1 and r["contas"] > 0
    assert _conta(owner_engine, Escola) == reais
    assert _conta(owner_engine, Usuario) == contas_reais
    assert seed.remover() == {"escolas": 0, "contas": 0}  # rodar de novo não faz nada


def test_remover_recusa_escola_com_conta_de_fora(mundo, demo, owner_engine):
    """Se alguém de verdade foi cadastrado na escola de demonstração, ela parece real: nada é apagado."""
    with Session(owner_engine) as db, db.begin():
        real = db.scalars(select(Usuario).where(Usuario.email == "prof.a@teste.com")).one()
        db.add(UsuarioPerfil(usuario_id=real.id, escola_id=demo, papel=Papel.professor))
    with pytest.raises(SystemExit, match="parece real"):
        seed.remover()
    assert _conta(owner_engine, Escola, Escola.id == demo) == 1


def test_producao_exige_confirmacao_e_nao_simula(monkeypatch):
    monkeypatch.setattr(get_settings(), "env", "prod")
    with pytest.raises(SystemExit, match="--confirmar"):
        seed.remover()
    with pytest.raises(SystemExit, match="produção"):
        seed.simular_semana()


def test_simular_sem_demonstracao_avisa():
    with pytest.raises(SystemExit, match="python -m app.seed"):
        seed.simular_semana()


def test_simular_completa_a_semana_e_e_idempotente(demo, owner_engine):
    with Session(owner_engine) as db, db.begin():
        p = db.scalars(
            select(Periodo)
            .join(AnoLetivo, AnoLetivo.id == Periodo.ano_letivo_id)
            .where(Periodo.escola_id == demo, Periodo.numero == 4, AnoLetivo.ano == 2026)
        ).one()
        corte, hoje = p.inicio + timedelta(days=10), p.inicio + timedelta(days=24)
        # volta a demonstração no tempo: apaga o que o seed lançou depois do corte
        db.execute(delete(Aula).where(Aula.escola_id == demo, Aula.data > corte))
        db.execute(delete(Avaliacao).where(Avaliacao.periodo_id == p.id))
        db.execute(delete(Aviso).where(Aviso.escola_id == demo))
        periodo_id, inicio = p.id, p.inicio
    n = seed.simular_semana(hoje)
    dias = sum(1 for i in range(11, 25) if (inicio + timedelta(days=i)).weekday() in (1, 3))
    atribuicoes = 6 * 4  # turmas x disciplinas do seed
    assert n == {"aulas": dias * atribuicoes, "avaliacoes": atribuicoes, "avisos": 1}  # só a Prova 1 já passou
    assert _conta(owner_engine, Aula, Aula.escola_id == demo, Aula.data > hoje) == 0
    assert _conta(owner_engine, Avaliacao, Avaliacao.periodo_id == periodo_id, Avaliacao.nome == "Prova 1") == 24
    assert seed.simular_semana(hoje) == {"aulas": 0, "avaliacoes": 0, "avisos": 0}
