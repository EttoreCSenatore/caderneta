#!/usr/bin/env python3
"""Gera o PACOTE PARA REVISÃO JURÍDICA desta instalação: um documento único (HTML para imprimir em PDF, e Markdown).

    python3 scripts/gerar-pacote-juridico.py --instalacao instalacao.json --saida pacote-juridico

O arquivo `instalacao.json` traz os dados desta escola e desta operadora (modelo em `.lgpd/pacote/instalacao.exemplo.json`).
O que faltar aparece como [A PREENCHER: campo]. Só usa a biblioteca padrão do Python.

Reúne: carta, ficha da instalação, perguntas ao advogado, pontos do contrato de operação, modelo de parecer e os anexos
(mapa de dados, política de privacidade e termos desta instalação, ROPA, RIPD, LIAs, plano de incidentes, lacunas).
"""

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LGPD = RAIZ / ".lgpd"
PACOTE = LGPD / "pacote"

# (id, título curto, arquivo(s) ou função)
SECOES = [
    ("carta", "1. Carta", [PACOTE / "01-carta.md"]),
    ("ficha", "2. Ficha da instalação", [PACOTE / "02-ficha-instalacao.md"]),
    ("perguntas", "3. Perguntas ao(à) advogado(a)", [PACOTE / "03-perguntas.md"]),
    ("contrato", "4. Contrato de operação: pontos mínimos", [PACOTE / "04-contrato-de-operacao.md"]),
    ("parecer", "5. Modelo de parecer e checklist", [PACOTE / "05-parecer.md"]),
    ("anexo-a", "Anexo A. Mapa de dados", [LGPD / "data-map.md"]),
    ("anexo-b", "Anexo B. Política de privacidade", "legal:privacidade"),
    ("anexo-c", "Anexo C. Termos de uso", "legal:termos"),
    ("anexo-d", "Anexo D. ROPA", [LGPD / "ROPA.md"]),
    ("anexo-e", "Anexo E. RIPD", [LGPD / "RIPD.md"]),
    ("anexo-f", "Anexo F. Testes de legítimo interesse (LIA)", sorted((LGPD / "lia").glob("*.md"))),
    ("anexo-g", "Anexo G. Plano de resposta a incidentes", [LGPD / "incidentes" / "runbook.md"]),
    ("anexo-h", "Anexo H. Lacunas e pendências", [LGPD / "gaps.md"]),
]


def le_texto_legal(doc: str, dados: dict) -> str:
    pasta = dados.get("textos_legais_dir") or ""
    arq = Path(pasta) / f"{doc}.md" if pasta else None
    arq = arq if arq and arq.is_file() else RAIZ / "api" / "app" / "legal" / f"{doc}.md"
    bruto = arq.read_text(encoding="utf-8")
    meta, corpo = {}, bruto
    if bruto.startswith("---"):
        _, cab, corpo = bruto.split("---", 2)
        meta = dict(linha.split(":", 1) for linha in cab.strip().splitlines())
        meta = {k.strip(): v.strip() for k, v in meta.items()}
    nome = dados.get("operadora_nome")
    operadora = f"**{nome}**" + (f" ({dados['operadora_contato']})" if dados.get("operadora_contato") else "") if nome else "[A PREENCHER: operadora]"
    corpo = corpo.replace("{{operadora}}", operadora)
    return f"> Versão **{meta.get('versao', '?')}** · situação: **{meta.get('status', '?')}** · arquivo: `{arq.name}`\n\n" + corpo.strip()


def versao_projeto() -> str:
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        h = "sem git"
    m = re.search(r'^version\s*=\s*"([^"]+)"', (RAIZ / "api" / "pyproject.toml").read_text(), re.M)
    return f"{m.group(1) if m else '?'} ({h})"


def preenche(texto: str, dados: dict, faltando: set) -> str:
    def troca(m: re.Match) -> str:
        campo = m.group(1)
        v = dados.get(campo)
        if v in (None, ""):
            faltando.add(campo)
            return f"[A PREENCHER: {campo}]"
        return str(v)

    return re.sub(r"\{\{(\w+)\}\}", troca, texto)


# --- Markdown mínimo para HTML ------------------------------------------------------------------------------


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)

    def link(m: re.Match) -> str:
        txt, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "#")):
            return f'<a href="{url}">{txt}</a>'
        return txt  # link relativo a arquivo do repositório: sem destino dentro do pacote

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)


def md_para_html(md: str) -> str:
    out: list[str] = []
    linhas = md.splitlines()
    i = 0
    while i < len(linhas):
        l = linhas[i]
        if l.startswith("```"):
            i += 1
            bloco = []
            while i < len(linhas) and not linhas[i].startswith("```"):
                bloco.append(linhas[i])
                i += 1
            out.append("<pre>" + html.escape("\n".join(bloco)) + "</pre>")
        elif re.match(r"^#{1,4} ", l):
            n = len(l) - len(l.lstrip("#"))
            out.append(f"<h{n}>{inline(l[n + 1:])}</h{n}>")
        elif l.startswith("|"):
            linhas_t = []
            while i < len(linhas) and linhas[i].startswith("|"):
                linhas_t.append(linhas[i])
                i += 1
            i -= 1
            cel = lambda s: [c.strip() for c in s.strip().strip("|").split("|")]  # noqa: E731
            cab = cel(linhas_t[0])
            corpo = [cel(x) for x in linhas_t[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cab) + "</tr></thead><tbody>")
            for r in corpo:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
        elif l.startswith(">"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith(">"):
                bloco.append(linhas[i].lstrip(">").strip())
                i += 1
            i -= 1
            out.append("<blockquote>" + inline(" ".join(bloco)) + "</blockquote>")
        elif re.match(r"^\s*([-*]|\d+\.) ", l):
            ordenada = bool(re.match(r"^\s*\d+\.", l))
            itens = []
            while i < len(linhas) and re.match(r"^\s*([-*]|\d+\.) ", linhas[i]):
                x = re.sub(r"^\s*([-*]|\d+\.) ", "", linhas[i])
                x = x.replace("[ ]", "☐").replace("[x]", "☑")
                itens.append(f"<li>{inline(x)}</li>")
                i += 1
            i -= 1
            tag = "ol" if ordenada else "ul"
            out.append(f"<{tag}>" + "".join(itens) + f"</{tag}>")
        elif l.strip() in ("---", "***"):
            out.append("<hr>")
        elif l.strip():
            par = [l]
            while i + 1 < len(linhas) and linhas[i + 1].strip() and not re.match(r"^(#{1,4} |\||>|```|\s*([-*]|\d+\.) )", linhas[i + 1]):
                i += 1
                par.append(linhas[i])
            out.append("<p>" + inline(" ".join(par)) + "</p>")
        i += 1
    return "\n".join(out)


CSS = """
body{font:15px/1.55 system-ui,Segoe UI,Roboto,sans-serif;color:#1a1d29;max-width:860px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.7rem;border-bottom:2px solid #1d4ed8;padding-bottom:.3rem;margin-top:0}
h2{font-size:1.3rem;margin-top:2rem} h3{font-size:1.1rem;margin-top:1.5rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.88rem} th,td{border:1px solid #c7cddb;padding:.35rem .5rem;vertical-align:top;text-align:left}
th{background:#eef2fb} code{background:#eef2fb;padding:0 .25rem;border-radius:3px;font-size:.9em} pre{background:#f3f5fa;padding:.75rem;overflow:auto;font-size:.8rem}
blockquote{border-left:4px solid #e0b100;background:#fff8e1;margin:1rem 0;padding:.5rem 1rem}
section{page-break-before:always}
.capa{text-align:center;padding:4rem 0 3rem} .capa h1{border:0;font-size:2.2rem} .falta{background:#ffe3e3;color:#a40000;font-weight:600}
nav li{margin:.2rem 0} a{color:#1d4ed8}
@media print{body{max-width:none;margin:0;font-size:11pt} nav a{color:inherit;text-decoration:none}}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--instalacao", help="arquivo JSON com os dados da instalação")
    ap.add_argument("--saida", default="pacote-juridico", help="pasta de saída (padrão: pacote-juridico)")
    a = ap.parse_args()
    dados = json.loads(Path(a.instalacao).read_text(encoding="utf-8")) if a.instalacao else {}
    dados.setdefault("data", date.today().strftime("%d/%m/%Y"))
    dados.setdefault("versao_projeto", versao_projeto())
    faltando: set[str] = set()

    md_total, partes_html, indice = [], [], []
    for sid, titulo, fonte in SECOES:
        if isinstance(fonte, str):
            texto = le_texto_legal(fonte.split(":")[1], dados)
        else:
            texto = "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in fonte)
        texto = preenche(texto, dados, faltando)
        md_total.append(texto)
        indice.append(f'<li><a href="#{sid}">{html.escape(titulo)}</a></li>')
        corpo = md_para_html(texto).replace("[A PREENCHER:", '<span class="falta">[A PREENCHER:').replace("]", "]</span>") if "[A PREENCHER:" in texto else md_para_html(texto)
        partes_html.append(f'<section id="{sid}">\n{corpo}\n</section>')

    nome = html.escape(str(dados.get("escola_nome") or "[A PREENCHER: escola_nome]"))
    capa = (
        f'<div class="capa"><h1>Pacote para revisão jurídica</h1><p><strong>Caderneta</strong> · {nome}</p>'
        f'<p>{html.escape(dados["data"])} · versão do software {html.escape(dados["versao_projeto"])}</p>'
        f"<p>Rascunho técnico: não é parecer jurídico.</p></div><nav><h2>Conteúdo</h2><ol>{''.join(indice)}</ol></nav>"
    )
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "pacote-juridico.md").write_text("\n\n\n".join(md_total), encoding="utf-8")
    (saida / "pacote-juridico.html").write_text(
        f'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Pacote para revisão jurídica: Caderneta</title>'
        f"<style>{CSS}</style><body>{capa}{''.join(partes_html)}</body></html>",
        encoding="utf-8",
    )
    print(f"Pacote gerado em {saida}/ (pacote-juridico.html para imprimir em PDF; pacote-juridico.md)")
    if faltando:
        print(f"Campos a preencher ({len(faltando)}): {', '.join(sorted(faltando))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
