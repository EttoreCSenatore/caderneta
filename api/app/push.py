"""Web Push sem conteúdo: o serviço de push (Google, Apple, Mozilla) só recebe "há novidade", nunca o texto.

Por privacidade (LGPD e ECA Digital) a mensagem vai vazia, assinada com VAPID (ES256). O service worker do app mostra
uma notificação genérica ("Você tem novidades") e, ao tocar, abre o app, onde o conteúdo vive atrás do login. Assim nada
sobre o aluno passa por terceiros, e não é preciso guardar as chaves de criptografia do aparelho.
"""

import base64
import json
import logging
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from app.config import get_settings

log = logging.getLogger("caderneta.push")
# Serviços de push dos navegadores. O endereço vem do aparelho: só aceitamos estes domínios (evita SSRF).
SUFIXOS_PERMITIDOS = (
    ".googleapis.com",
    ".push.services.mozilla.com",
    ".push.apple.com",
    ".notify.windows.com",
)


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _d64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def gerar_chaves() -> tuple[str, str]:
    """(chave privada, chave pública) em base64url, prontas para as variáveis de ambiente."""
    k = ec.generate_private_key(ec.SECP256R1())
    privada = k.private_numbers().private_value.to_bytes(32, "big")
    publica = k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return _b64(privada), _b64(publica)


def ativo() -> bool:
    s = get_settings()
    return bool(s.vapid_private_key and s.vapid_public_key)


def chave_publica() -> str:
    return get_settings().vapid_public_key


def endpoint_valido(url: str) -> bool:
    """https, porta padrão e um serviço de push conhecido. Hosts extras (config) só para testes e redes internas."""
    if len(url) > 1000:
        return False
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    extras = {h.strip().lower() for h in get_settings().push_hosts_extra.split(",") if h.strip()}
    if host in extras:
        return p.scheme in ("http", "https")
    if p.scheme != "https" or p.port not in (None, 443) or p.username or p.password:
        return False
    return host == "web.push.apple.com" or host.endswith(SUFIXOS_PERMITIDOS)


def _jwt(audiencia: str) -> str:
    s = get_settings()
    d = int.from_bytes(_d64(s.vapid_private_key), "big")
    chave = ec.derive_private_key(d, ec.SECP256R1())
    cab = _b64(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    corpo = _b64(
        json.dumps(
            {"aud": audiencia, "exp": int(time.time()) + 12 * 3600, "sub": s.vapid_subject}, separators=(",", ":")
        ).encode()
    )
    assinatura = chave.sign(f"{cab}.{corpo}".encode(), ec.ECDSA(hashes.SHA256()))
    r, sv = decode_dss_signature(assinatura)
    return f"{cab}.{corpo}.{_b64(r.to_bytes(32, 'big') + sv.to_bytes(32, 'big'))}"


def envia(endpoint: str, ttl: int = 3600) -> int:
    """Manda um push vazio. Devolve o status HTTP (201 ok; 404/410 aparelho não existe mais; 0 falha de rede)."""
    if not ativo() or not endpoint_valido(endpoint):
        return 0
    p = urlsplit(endpoint)
    req = urllib.request.Request(  # noqa: S310 - endereço validado acima
        endpoint,
        data=b"",
        method="POST",
        headers={
            "Authorization": f"vapid t={_jwt(f'{p.scheme}://{p.netloc}')}, k={chave_publica()}",
            "TTL": str(ttl),
            "Urgency": "normal",
            "Content-Length": "0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        log.warning("falha de rede ao enviar push")
        return 0
