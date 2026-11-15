"""Senhas (Argon2id), tokens opacos, criptografia de campo (AES-256-GCM) e TOTP."""

import base64
import hashlib
import json
import os
import secrets
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
