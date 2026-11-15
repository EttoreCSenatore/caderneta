"""Regressão: o commit precisa acontecer antes de a resposta sair.

Com o escopo padrão ("request"), o FastAPI roda o fim das dependências com yield depois de enviar a
resposta. O navegador recebia o OK do login e chamava /auth/me antes de a sessão estar gravada (401).
"""

from fastapi.routing import APIRoute

from app.db import get_db
from app.routers import alunos, auth, convites, escola, importacao, turmas


def _deps(dep):
    for d in dep.dependencies:
        yield d
        yield from _deps(d)


def test_get_db_sempre_com_escopo_de_funcao():
    usos = 0
    rotas = [r for m in (alunos, auth, convites, escola, importacao, turmas) for r in m.router.routes]
    for rota in rotas:
        if not isinstance(rota, APIRoute):
            continue
        for d in _deps(rota.dependant):
            if d.call is get_db:
                usos += 1
                assert d.scope == "function", f"{rota.path}: get_db sem scope='function'"
    assert usos > 20
