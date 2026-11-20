"""Versões e Novidades (MO.3): lê o releases.yaml, fonte única da versão e das notas de cada versão."""

import datetime as dt
import re
from functools import cache
from pathlib import Path

import yaml

from app.models import Papel

TIPOS = ("novo", "melhoria", "correcao", "seguranca")
PUBLICOS = ("equipe", "familia")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

# Em desenvolvimento o arquivo está na raiz do repositório; na imagem, ao lado do pacote app (/app/releases.yaml).
_AQUI = Path(__file__).resolve().parent
CANDIDATOS = (_AQUI.parent / "releases.yaml", _AQUI.parent.parent / "releases.yaml")


def publico_de(papel: Papel) -> str:
    return "familia" if papel in (Papel.responsavel, Papel.aluno) else "equipe"


def chave(versao: str) -> tuple[int, int, int]:
    m = SEMVER.match(versao)
    if not m:
        raise ValueError(f"versão fora do formato X.Y.Z: {versao!r}")
    return int(m[1]), int(m[2]), int(m[3])


def valida(versoes: list[dict]) -> None:
    """Formato e ordem: o arquivo é escrito à mão, então os erros precisam ser claros."""
    if not versoes:
        raise ValueError("releases.yaml sem nenhuma versão")
    anterior = None
    for v in versoes:
        nome = v.get("versao")
        if not isinstance(nome, str):
            raise ValueError(f"versão sem o campo 'versao' (use aspas se for preciso): {v!r}")
        atual = chave(nome)
        if anterior is not None and atual >= anterior:
            raise ValueError(f"{nome}: as versões precisam estar da mais nova para a mais antiga, sem repetir")
        anterior = atual
        if not isinstance(v.get("data"), dt.date):
            raise ValueError(f"{nome}: 'data' precisa ser AAAA-MM-DD")
        if not str(v.get("titulo") or "").strip():
            raise ValueError(f"{nome}: falta o 'titulo'")
        itens = v.get("itens")
        if not itens:
            raise ValueError(f"{nome}: falta a lista 'itens'")
        for i in itens:
            if i.get("tipo") not in TIPOS:
                raise ValueError(f"{nome}: tipo {i.get('tipo')!r} inválido (use {', '.join(TIPOS)})")
            pub = i.get("publico")
            if not pub or any(p not in PUBLICOS for p in pub):
                raise ValueError(f"{nome}: publico {pub!r} inválido (use {', '.join(PUBLICOS)})")
            if not str(i.get("texto") or "").strip():
                raise ValueError(f"{nome}: item sem 'texto'")


@cache
def carrega() -> tuple[dict, ...]:
    for c in CANDIDATOS:
        if c.is_file():
            versoes = yaml.safe_load(c.read_text(encoding="utf-8")) or []
            valida(versoes)
            return tuple(versoes)
    raise FileNotFoundError("releases.yaml não encontrado (" + ", ".join(str(c) for c in CANDIDATOS) + ")")


def versao_atual() -> str:
    return carrega()[0]["versao"]


def para(publico: str) -> list[dict]:
    """Versões com os itens deste público; versões sem item para ele somem da lista."""
    saida = []
    for v in carrega():
        itens = [
            {"tipo": i["tipo"], "texto": " ".join(i["texto"].split())} for i in v["itens"] if publico in i["publico"]
        ]
        if itens:
            saida.append({"versao": v["versao"], "data": v["data"].isoformat(), "titulo": v["titulo"], "itens": itens})
    return saida
