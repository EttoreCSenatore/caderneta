"""MO.3: versão única (releases.yaml) e página Novidades filtrada por público."""

import datetime as dt
import json
import tomllib
from pathlib import Path

import pytest

from app import versoes
from tests.conftest import Cliente

RAIZ = Path(__file__).resolve().parents[2]


def test_versao_e_a_mesma_em_todo_lugar():
    """O topo do releases.yaml manda: pyproject, package.json e /api/saude acompanham."""
    atual = versoes.versao_atual()
    assert tomllib.loads((RAIZ / "api" / "pyproject.toml").read_text())["project"]["version"] == atual
    assert json.loads((RAIZ / "web" / "package.json").read_text())["version"] == atual
    assert json.loads((RAIZ / "web" / "package-lock.json").read_text())["version"] == atual


def test_saude_e_publica_e_diz_a_versao():
    r = Cliente().get("/api/saude")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "versao": versoes.versao_atual()}


def test_data_da_versao_mais_nova_nao_esta_no_futuro():
    assert versoes.carrega()[0]["data"] <= dt.date.today() + dt.timedelta(days=1)


def test_novidades_exige_login(mundo):
    assert Cliente().get("/api/novidades").status_code == 401


def test_cada_papel_ve_so_o_seu_publico(mundo, entrar):
    publicos = {
        "admin.a@teste.com": "equipe",
        "prof.a@teste.com": "equipe",
        "mae.a@teste.com": "familia",
        "aluno.a@teste.com": "familia",
    }
    for email, publico in publicos.items():
        d = entrar(email).get("/api/novidades").json()
        assert d["versao_atual"] == versoes.versao_atual()
        assert d["versoes"] == versoes.para(publico)
        assert d["versoes"], email
    # um item só da equipe não aparece para a família
    so_equipe = {i["texto"] for v in versoes.para("equipe") for i in v["itens"]} - {
        i["texto"] for v in versoes.para("familia") for i in v["itens"]
    }
    assert so_equipe
    textos_familia = {
        i["texto"] for v in entrar("mae.a@teste.com").get("/api/novidades").json()["versoes"] for i in v["itens"]
    }
    assert not so_equipe & textos_familia


def _v(versao: str, **extra) -> dict:
    base = {
        "versao": versao,
        "data": dt.date(2026, 1, 1),
        "titulo": "T",
        "itens": [{"tipo": "novo", "publico": ["equipe"], "texto": "x"}],
    }
    return base | extra


@pytest.mark.parametrize(
    ("lista", "erro"),
    [
        ([], "nenhuma versão"),
        ([_v("1.0")], "X.Y.Z"),
        ([_v("1.0.0"), _v("1.1.0")], "mais nova para a mais antiga"),
        ([_v("1.0.0"), _v("1.0.0")], "mais nova para a mais antiga"),
        ([_v("1.0.0", data="ontem")], "AAAA-MM-DD"),
        ([_v("1.0.0", titulo="")], "titulo"),
        ([_v("1.0.0", itens=[])], "itens"),
        ([_v("1.0.0", itens=[{"tipo": "outro", "publico": ["equipe"], "texto": "x"}])], "tipo"),
        ([_v("1.0.0", itens=[{"tipo": "novo", "publico": ["todos"], "texto": "x"}])], "publico"),
        ([_v("1.0.0", itens=[{"tipo": "novo", "publico": ["equipe"], "texto": " "}])], "texto"),
    ],
)
def test_validacao_aponta_o_erro(lista, erro):
    with pytest.raises(ValueError, match=erro):
        versoes.valida(lista)


def test_arquivo_do_repositorio_e_valido():
    versoes.valida(list(versoes.carrega()))
