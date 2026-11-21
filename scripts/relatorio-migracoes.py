#!/usr/bin/env python3
"""Relatório das migrations de um PR (MO.5): o SQL que cada migration nova roda e o que merece atenção.

    python3 scripts/relatorio-migracoes.py --base origin/main --saida relatorio.md

Não conecta no banco: o SQL vem do modo offline do Alembic (`alembic upgrade A:B --sql`). Aponta:
- operações que apagam ou reescrevem dados (DROP, DELETE, TRUNCATE, mudança de tipo, renomeação, REVOKE);
- migrations que já estavam na base e foram alteradas ou apagadas (o upgrade delas já rodou em algum banco).
Sai com 0 sempre: é um relatório para quem revisa. A trava é o teste de ida e volta (api/tests/test_migracoes.py).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
API = RAIZ / "api"
PASTA = "api/migrations/versions"
ATENCAO = [
    (r"\bDROP\s+TABLE\b", "apaga uma tabela"),
    (r"\bDROP\s+COLUMN\b", "apaga uma coluna"),
    (r"\bDROP\s+(TYPE|FUNCTION|POLICY|INDEX)\b", "apaga tipo, função, política ou índice"),
    (r"\bDELETE\s+FROM\b", "apaga linhas"),
    (r"\bTRUNCATE\b", "esvazia uma tabela"),
    (r"\bALTER\s+COLUMN\s+\S+\s+(SET\s+DATA\s+)?TYPE\b", "muda o tipo de uma coluna"),
    (r"\bRENAME\b", "renomeia algo (a versão anterior do app deixa de achar)"),
    (r"\bSET\s+NOT\s+NULL\b", "passa a exigir valor (falha se houver linha vazia)"),
    (r"\bREVOKE\b", "retira permissão"),
    (r"\bDISABLE\s+ROW\s+LEVEL\s+SECURITY\b", "desliga o isolamento entre escolas (RLS)"),
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, check=True, capture_output=True, text=True).stdout


def revisao(texto: str) -> tuple[str, str | None]:
    rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", texto, re.MULTILINE)
    down = re.search(r"^down_revision\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", texto, re.MULTILINE)
    if not rev or not down:
        raise ValueError("revision/down_revision não encontrados")
    return rev[1], down[1]


def sql_de(rev: str, down: str | None) -> str:
    alvo = f"{down}:{rev}" if down else f"base:{rev}"
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", alvo, "--sql"],
        check=False,
        cwd=API,
        capture_output=True,
        text=True,
    )
    if r.returncode:
        return f"-- não consegui gerar o SQL offline:\n{r.stderr.strip()[-1500:]}"
    return r.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args()
    mudancas = [
        linha.split("\t") for linha in git("diff", "--name-status", f"{a.base}...HEAD", "--", PASTA).splitlines()
    ]
    novas = [m[-1] for m in mudancas if m[0].startswith("A") and m[-1].endswith(".py")]
    mexidas = [(m[0][0], m[1]) for m in mudancas if m[0][0] in "MDR" and m[1].endswith(".py")]

    linhas = ["## Relatório de migrations", ""]
    if not novas and not mexidas:
        linhas.append("Nenhuma migration nova ou alterada neste PR.")
    alertas: list[str] = []
    for tipo, arq in mexidas:
        acao = {"M": "alterada", "D": "apagada", "R": "renomeada"}[tipo]
        alertas.append(
            f"`{Path(arq).name}` já estava na base e foi **{acao}**: o upgrade dela já rodou em bancos reais."
        )
    blocos: list[str] = []
    for arq in novas:
        rev, down = revisao((RAIZ / arq).read_text(encoding="utf-8"))
        sql = sql_de(rev, down)
        achados = sorted({motivo for padrao, motivo in ATENCAO if re.search(padrao, sql, re.IGNORECASE)})
        alertas += [f"`{rev}` {motivo}" for motivo in achados]
        blocos += [
            f"<details><summary><code>{rev}</code> ({Path(arq).name}){' ⚠️' if achados else ''}</summary>",
            "",
            "```sql",
            sql,
            "```",
            "</details>",
            "",
        ]
    if alertas:
        linhas += ["**Atenção:**", "", *[f"- {x}" for x in alertas], ""]
        linhas.append("Confira se há backup recente antes de aplicar e se a versão anterior do app ainda funciona.")
        linhas.append("")
    elif novas:
        linhas += ["Nenhuma operação que apague ou reescreva dados.", ""]
    if novas:
        linhas += [f"**SQL das migrations novas ({len(novas)}):**", "", *blocos]
        linhas.append(
            "O teste de ida e volta (`api/tests/test_migracoes.py`) confere que cada `downgrade()` desfaz tudo."
        )
    a.saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
