#!/usr/bin/env python3
"""Título e texto da release do GitHub de uma versão, a partir do releases.yaml (MO.3).

    python3 scripts/notas-versao.py              # versão mais nova: imprime "versão<TAB>título" e grava o texto
    python3 scripts/notas-versao.py 0.9.0 --texto notas.md

Precisa de PyYAML (vem com as dependências da API).
"""

import argparse
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
TIPOS = {"novo": "Novo", "melhoria": "Melhoria", "correcao": "Correção", "seguranca": "Segurança"}
PUBLICOS = {"equipe": "equipe", "familia": "famílias"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("versao", nargs="?")
    ap.add_argument("--texto", type=Path, help="arquivo onde gravar o texto da release")
    a = ap.parse_args()
    versoes = yaml.safe_load((RAIZ / "releases.yaml").read_text(encoding="utf-8"))
    v = next((x for x in versoes if x["versao"] == a.versao), None) if a.versao else versoes[0]
    if v is None:
        print(f"versão {a.versao} não está no releases.yaml", file=sys.stderr)
        return 1
    linhas = [f"_{v['data'].isoformat()}_", ""]
    for tipo, rotulo in TIPOS.items():
        itens = [i for i in v["itens"] if i["tipo"] == tipo]
        if not itens:
            continue
        linhas += [f"### {rotulo}", ""]
        for i in itens:
            quem = " e ".join(PUBLICOS[p] for p in i["publico"])
            linhas.append(f"- {' '.join(i['texto'].split())} _({quem})_")
        linhas.append("")
    linhas.append("Histórico completo: [`releases.yaml`](releases.yaml) e a página **Novidades** dentro do app.")
    texto = "\n".join(linhas) + "\n"
    if a.texto:
        a.texto.write_text(texto, encoding="utf-8")
    else:
        sys.stdout.write(texto)
    print(f"{v['versao']}\t{v['titulo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
