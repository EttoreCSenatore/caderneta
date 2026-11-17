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
from cryptography.exceptions import InvalidTag
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


def _decodifica(chave_b64: str) -> bytes:
    key = base64.urlsafe_b64decode(chave_b64)
    if len(key) != 32:
        raise RuntimeError("As chaves de dados precisam ter 32 bytes em base64")
    return key


@lru_cache
def _chaves() -> tuple[AESGCM, ...]:
    """Chave atual primeiro, depois as antigas (só para ler).

    Dev/test sem chave: chave derivada fixa (config.py bloqueia em produção).
    """
    s = get_settings()
    atual = _decodifica(s.data_key) if s.data_key else hashlib.sha256(b"caderneta-dev-key").digest()
    antigas = [_decodifica(k.strip()) for k in s.data_keys_antigas.split(",") if k.strip()]
    return tuple(AESGCM(k) for k in [atual, *antigas])


def _aes() -> AESGCM:
    return _chaves()[0]


def _abre(dado: bytes, contexto: str) -> bytes:
    """Decifra com a chave atual e, se falhar a autenticação, com as antigas (rotação em andamento)."""
    for k in _chaves():
        try:
            return k.decrypt(dado[:12], dado[12:], contexto.encode())
        except InvalidTag:
            continue
    raise InvalidTag("nenhuma chave de dados abriu o conteúdo")


def na_chave_atual(dado: bytes, contexto: str) -> bool:
    """True se o conteúdo já está cifrado com a chave atual (usado pela rotação)."""
    try:
        _aes().decrypt(dado[:12], dado[12:], contexto.encode())
        return True
    except InvalidTag:
        return False


def cifra(valor: str, contexto: str) -> bytes:
    """AES-GCM; `contexto` (ex.: id do aluno) entra como dado associado, impedindo trocar cifras entre linhas."""
    nonce = os.urandom(12)
    return nonce + _aes().encrypt(nonce, valor.encode(), contexto.encode())


def decifra(dado: bytes, contexto: str) -> str:
    return _abre(dado, contexto).decode()


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


def passo_totp(secret: str, codigo: str, ultimo: int | None) -> int | None:
    """Passo de 30 s em que o código vale (janela de +-1), ou None. Rejeita passo já usado (reuso do mesmo código)."""
    codigo = codigo.strip().replace(" ", "")
    if not codigo.isdigit():
        return None
    if not get_settings().totp_anti_reuso:
        ultimo = None
    try:
        t = pyotp.TOTP(secret)
        agora = int(time.time()) // 30
        for passo in (agora, agora - 1, agora + 1):
            if hmac.compare_digest(t.at(passo * 30), codigo):
                return passo if ultimo is None or passo > ultimo else None
    except ValueError:  # segredo corrompido: trata como código inválido, sem erro 500
        return None
    return None


def cifra_bytes(dado: bytes, contexto: str) -> bytes:
    """Como `cifra`, para arquivos: nonce (12) + texto cifrado + tag, com o contexto como dado associado."""
    nonce = os.urandom(12)
    return nonce + _aes().encrypt(nonce, dado, contexto.encode())


def decifra_bytes(dado: bytes, contexto: str) -> bytes:
    return _abre(dado, contexto)


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
