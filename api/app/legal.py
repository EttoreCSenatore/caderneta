"""Textos legais (política de privacidade e termos de uso), versionados em `app/legal/*.md`.

Cada arquivo começa com `versao`, `titulo` e `status` (`rascunho` até o parecer jurídico). Mudou o texto de forma
relevante? Troque a `versao`: todo mundo passa a ver a tela de confirmação de novo no próximo acesso.
"""

from functools import lru_cache
from pathlib import Path

from app.config import get_settings

DOCS = ("privacidade", "termos")
PASTA = Path(__file__).parent / "legal"


def operadora() -> str:
    """Quem opera esta instalação, como aparece nos textos (configurado por CADERNETA_OPERADORA_*)."""
    s = get_settings()
    if not s.operadora_nome:
        return "[OPERADORA DESTA INSTALAÇÃO: INFORMAR NA CONFIGURAÇÃO]"
    return f"**{s.operadora_nome}**" + (f" ({s.operadora_contato})" if s.operadora_contato else "")


def carrega(doc: str) -> dict:
    """Texto com as variáveis desta instalação preenchidas."""
    c = dict(_le(doc))
    c["texto"] = c["texto"].replace("{{operadora}}", operadora())
    return c


@lru_cache
def _le(doc: str) -> dict:
    if doc not in DOCS:
        raise KeyError(doc)
    bruto = (PASTA / f"{doc}.md").read_text(encoding="utf-8")
    _, cab, corpo = bruto.split("---", 2)
    meta = dict(linha.split(":", 1) for linha in cab.strip().splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    return {
        "doc": doc,
        "versao": meta["versao"],
        "titulo": meta["titulo"],
        "status": meta["status"],
        "texto": corpo.strip(),
    }
