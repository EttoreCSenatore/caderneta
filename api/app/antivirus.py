"""Verificação de arquivos com ClamAV (daemon `clamd`, protocolo INSTREAM).

Falha fechada: com o antivírus ligado, se o `clamd` estiver fora do ar ou responder algo inesperado, o arquivo
é recusado. Nunca passamos um arquivo sem verificação só porque o serviço caiu.
"""

import logging
import socket
import struct

from fastapi import HTTPException

from app.config import get_settings

log = logging.getLogger("caderneta.antivirus")
_BLOCO = 64 * 1024


def verifica(dados: bytes) -> None:
    """Levanta 422 se encontrar vírus e 503 se não conseguir verificar. Não faz nada com o antivírus desligado."""
    s = get_settings()
    if s.antivirus != "clamav":
        return
    try:
        with socket.create_connection((s.clamav_host, s.clamav_port), timeout=s.clamav_timeout_s) as sock:
            sock.settimeout(s.clamav_timeout_s)
            sock.sendall(b"zINSTREAM\0")
            for i in range(0, len(dados), _BLOCO):
                parte = dados[i : i + _BLOCO]
                sock.sendall(struct.pack("!I", len(parte)) + parte)
            sock.sendall(struct.pack("!I", 0))
            resposta = b""
            while not resposta.endswith(b"\0") and len(resposta) < 4096:
                pedaco = sock.recv(1024)
                if not pedaco:
                    break
                resposta += pedaco
    except OSError:
        log.exception("antivírus indisponível")
        raise HTTPException(503, "Não foi possível verificar o arquivo agora. Tente de novo em instantes.") from None
    texto = resposta.rstrip(b"\0\n").decode("utf-8", "replace")
    if texto.endswith("FOUND"):
        log.warning("arquivo recusado pelo antivírus")  # sem o nome da assinatura nem do arquivo no log
        raise HTTPException(422, "O antivírus encontrou um problema neste arquivo e ele não foi aceito.")
    if not texto.endswith("OK"):
        log.error("resposta inesperada do clamd: %s", texto[:80])
        raise HTTPException(503, "Não foi possível verificar o arquivo agora. Tente de novo em instantes.")
