"""Limite de taxa por janela fixa, guardado no banco (vale para vários processos da API).

O contador usa uma transação própria e já confirmada: continua valendo mesmo se a requisição depois falhar
(404, 401...), que é justamente o caso do abuso.
Atrás de um proxy reverso, rode a API com `--proxy-headers --forwarded-allow-ips=<ip do proxy>`; senão o IP
visto é o do proxy e todo mundo cai no mesmo limite.
"""

import hashlib
import time

from fastapi import Request
from sqlalchemy import text

from app.config import get_settings
from app.db import get_engine


def _quem(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"


def excedeu(request: Request, escopo: str, limite: int, janela_s: int, quem: str | None = None) -> bool:
    """Conta mais uma tentativa de `quem` (padrão: o IP) em `escopo`; True se passou de `limite` na janela."""
    if not get_settings().rate_limit:
        return False
    chave = f"{escopo}:{hashlib.sha256((quem or _quem(request)).lower().encode()).hexdigest()[:40]}"
    janela = int(time.time()) // janela_s * janela_s
    with get_engine().begin() as conn:
        n = conn.execute(
            text(
                "INSERT INTO limite_taxa (chave, janela, n) VALUES (:c, :j, 1) "
                "ON CONFLICT (chave, janela) DO UPDATE SET n = limite_taxa.n + 1 RETURNING n"
            ),
            {"c": chave, "j": janela},
        ).scalar_one()
    return n > limite
