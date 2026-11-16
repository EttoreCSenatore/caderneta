"""Senhas (Argon2id), tokens opacos, criptografia de campo (AES-256-GCM) e TOTP."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from functools import lru_cache

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

_ph = PasswordHasher()  # Argon2id com parâmetros recomendados pela RFC 9106
_DUMMY_HASH = _ph.hash("senha-que-nao-existe")


def hash_senha(senha: str) -> str:
    return _ph.hash(senha)


def verifica_senha(hash_: str | None, senha: str) -> bool:
    """Tempo constante mesmo quando o usuário não existe (evita descobrir e-mails pelo tempo)."""
    try:
        return _ph.verify(hash_ or _DUMMY_HASH, senha) and hash_ is not None
    except (VerifyMismatchError, InvalidHashError):
        return False


def senha_fraca(senha: str) -> str | None:
    if len(senha) < 10:
        return "A senha precisa ter pelo menos 10 caracteres."
    if senha.isdigit() or senha.isalpha():
        return "Misture letras com números ou símbolos."
    return None


def novo_token() -> tuple[str, str]:
    """Retorna (token para o usuário, hash SHA-256 para o banco)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@lru_cache
def _aes() -> AESGCM:
    key_b64 = get_settings().data_key
    if key_b64:
        key = base64.urlsafe_b64decode(key_b64)
    else:  # dev/test: chave derivada fixa, nunca usada em produção (config.py bloqueia)
        key = hashlib.sha256(b"caderneta-dev-key").digest()
    if len(key) != 32:
        raise RuntimeError("CADERNETA_DATA_KEY precisa ter 32 bytes em base64")
    return AESGCM(key)


def cifra(valor: str, contexto: str) -> bytes:
    """AES-GCM; `contexto` (ex.: id do aluno) entra como dado associado, impedindo trocar cifras entre linhas."""
    nonce = os.urandom(12)
    return nonce + _aes().encrypt(nonce, valor.encode(), contexto.encode())


def decifra(dado: bytes, contexto: str) -> str:
    return _aes().decrypt(dado[:12], dado[12:], contexto.encode()).decode()


def cifra_json(valor: dict, contexto: str) -> bytes:
    return cifra(json.dumps(valor, ensure_ascii=False), contexto)


def decifra_json(dado: bytes, contexto: str) -> dict:
    return json.loads(decifra(dado, contexto))


def novo_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="Caderneta")


def verifica_totp(secret: str, codigo: str) -> bool:
    codigo = codigo.strip().replace(" ", "")
    try:
        return codigo.isdigit() and pyotp.TOTP(secret).verify(codigo, valid_window=1)
    except ValueError:  # segredo corrompido: trata como código inválido, sem erro 500
        return False


def cifra_bytes(dado: bytes, contexto: str) -> bytes:
    """Como `cifra`, para arquivos: nonce (12) + texto cifrado + tag, com o contexto como dado associado."""
    nonce = os.urandom(12)
    return nonce + _aes().encrypt(nonce, dado, contexto.encode())


def decifra_bytes(dado: bytes, contexto: str) -> bytes:
    return _aes().decrypt(dado[:12], dado[12:], contexto.encode())


def _chave_links() -> bytes:
    return hashlib.sha256(b"links-assinados:" + _chave_bruta()).digest()


def _chave_bruta() -> bytes:
    key_b64 = get_settings().data_key
    return base64.urlsafe_b64decode(key_b64) if key_b64 else hashlib.sha256(b"caderneta-dev-key").digest()


def assina_link(carga: dict, validade_s: int) -> str:
    """Token curto e assinado (HMAC-SHA256): `<carga>.<assinatura>`, com expiração embutida."""
    corpo = dict(carga, e=int(time.time()) + validade_s)
    b = base64.urlsafe_b64encode(json.dumps(corpo, separators=(",", ":")).encode()).rstrip(b"=")
    sig = hmac.new(_chave_links(), b, hashlib.sha256).digest()
    return b.decode() + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def verifica_link(token: str) -> dict | None:
    """Devolve a carga se a assinatura é válida e o link não expirou; senão None."""
    try:
        b, sig = token.split(".", 1)
        esperado = hmac.new(_chave_links(), b.encode(), hashlib.sha256).digest()
        recebido = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))
        if not hmac.compare_digest(esperado, recebido):
            return None
        carga = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        return carga if carga.get("e", 0) >= time.time() else None
    except (ValueError, TypeError, KeyError):
        return None
