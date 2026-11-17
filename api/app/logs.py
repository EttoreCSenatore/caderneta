"""Logs de acesso sem dado pessoal além do necessário.

O log de acesso do uvicorn grava a URL inteira. Aqui tiramos a **query string** (busca por nome de aluno, filtros) e
trocamos por um marcador os **segredos que viajam na URL** (convite, link do calendário, código de conferência).
O IP do cliente continua, porque é o registro de acesso e a base da investigação de incidentes (prazo a definir, T5).
"""

import logging
import re

_SEGREDOS = (
    (re.compile(r"(/convites/abrir/)[^/\s?]+"), r"\1<token>"),
    (re.compile(r"(/calendario/ical/)[^/\s?]+(\.ics)"), r"\1<token>\2"),
    (re.compile(r"(/historico/verificar/)[^/\s?]+"), r"\1<codigo>"),
)


def limpa_caminho(caminho: str) -> str:
    caminho = caminho.split("?", 1)[0]
    for rx, sub in _SEGREDOS:
        caminho = rx.sub(sub, caminho)
    return caminho


class FiltroAcesso(logging.Filter):
    """Reescreve o caminho nos registros de acesso do uvicorn: args = (cliente, método, caminho, versão, status)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple) and len(record.args) >= 3:
            args = list(record.args)
            args[2] = limpa_caminho(str(args[2]))
            record.args = tuple(args)
        return True


def configura_logs() -> None:
    alvo = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, FiltroAcesso) for f in alvo.filters):
        alvo.addFilter(FiltroAcesso())
