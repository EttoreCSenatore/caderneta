"""MO.5: toda migration desfaz o que fez. Desce uma a uma até o início, sobe de novo e o esquema tem de ser igual.

Pega o `downgrade()` esquecido ou incompleto (coluna, índice, política de RLS, função ou permissão que sobra ou falta)
antes que alguém precise dele numa volta de versão em produção.
"""

import os

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.config import get_settings

API = os.path.dirname(os.path.dirname(__file__))

CONSULTAS = {
    "colunas": """SELECT table_name, column_name, data_type, is_nullable, coalesce(column_default, '')
                  FROM information_schema.columns WHERE table_schema = 'public'""",
    "indices": "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'",
    "restricoes": """SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid)
                     FROM pg_constraint WHERE connamespace = 'public'::regnamespace""",
    "rls": """SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class
              WHERE relnamespace = 'public'::regnamespace AND relkind = 'r'""",
    "politicas": "SELECT tablename, policyname, cmd, coalesce(qual, ''), coalesce(with_check, '') FROM pg_policies",
    "funcoes": """SELECT p.proname, pg_get_function_identity_arguments(p.oid), p.prosecdef FROM pg_proc p
                  WHERE p.pronamespace = 'public'::regnamespace
                  AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = p.oid AND d.deptype = 'e')""",
    "tipos": """SELECT t.typname, string_agg(e.enumlabel, ',' ORDER BY e.enumsortorder) FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid WHERE t.typnamespace = 'public'::regnamespace GROUP BY 1""",
    "permissoes": """SELECT table_name, privilege_type FROM information_schema.role_table_grants
                     WHERE grantee = 'caderneta_app' AND table_schema = 'public'""",
    "gatilhos": """SELECT event_object_table, trigger_name, action_timing, event_manipulation
                   FROM information_schema.triggers WHERE trigger_schema = 'public'""",
}


def _esquema(engine) -> dict[str, list[tuple]]:
    with engine.connect() as c:
        return {nome: sorted(tuple(r) for r in c.execute(text(sql))) for nome, sql in CONSULTAS.items()}


def _cfg() -> Config:
    cfg = Config(os.path.join(API, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(API, "migrations"))
    cfg.attributes["url"] = get_settings().owner_database_url
    return cfg


def _diferenca(antes: dict, depois: dict) -> str:
    linhas = []
    for nome in CONSULTAS:
        a, d = set(antes[nome]), set(depois[nome])
        linhas += [f"{nome}: sumiu {x}" for x in sorted(a - d)] + [f"{nome}: sobrou {x}" for x in sorted(d - a)]
    return "\n".join(linhas)


def _versao(engine) -> str | None:
    with engine.connect() as c:
        existe = c.execute(text("SELECT to_regclass('public.alembic_version')")).scalar()
        return c.execute(text("SELECT version_num FROM alembic_version")).scalar() if existe else None


def test_cada_downgrade_volta_ao_esquema_da_versao_anterior(owner_engine):
    """Sobe uma a uma guardando o esquema de cada versão; depois desce uma a uma e compara a cada passo.

    Comparar só no fim não basta: uma coluna esquecida num downgrade some quando uma migration mais antiga apaga a
    tabela inteira.
    """
    cfg = _cfg()
    revisoes = [r.revision for r in ScriptDirectory.from_config(cfg).walk_revisions()][::-1]  # da mais antiga
    try:
        command.downgrade(cfg, "base")
        esquemas = {None: _esquema(owner_engine)}
        assert [t for t, *_ in esquemas[None]["colunas"] if t != "alembic_version"] == [], "sobrou tabela na base"
        assert esquemas[None]["funcoes"] == [] and esquemas[None]["tipos"] == []
        for rev in revisoes:
            command.upgrade(cfg, rev)
            esquemas[rev] = _esquema(owner_engine)
        anterior = [None, *revisoes[:-1]]
        for rev, antes in zip(reversed(revisoes), reversed(anterior), strict=True):
            command.downgrade(cfg, "-1")
            assert _versao(owner_engine) == antes, f"o downgrade de {rev} não voltou para {antes}"
            atual = _esquema(owner_engine)
            assert atual == esquemas[antes], f"downgrade de {rev} incompleto:\n" + _diferenca(esquemas[antes], atual)
    finally:
        command.upgrade(cfg, "head")  # os outros testes continuam com o esquema completo
    assert _esquema(owner_engine) == esquemas[revisoes[-1]]


def test_cada_migration_sobe_depois_de_descer_uma(owner_engine):
    """Descer e subir a última migration (o caso real: corrigir um deploy) deixa o esquema igual."""
    cfg = _cfg()
    completo = _esquema(owner_engine)
    command.downgrade(cfg, "-1")
    command.upgrade(cfg, "head")
    assert _esquema(owner_engine) == completo, _diferenca(completo, _esquema(owner_engine))
