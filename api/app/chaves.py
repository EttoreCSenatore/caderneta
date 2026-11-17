"""Rotação da chave de dados (AES-256-GCM): regrava com a chave atual tudo o que ainda está na chave antiga.

Procedimento (ver a página "Backups, chaves e logs" na documentação):
1. gere uma chave nova; ponha-a em `CADERNETA_DATA_KEY` e a antiga em `CADERNETA_DATA_KEYS_ANTIGAS`;
2. reinicie a API (ela passa a ler com as duas e gravar com a nova);
3. rode `python -m app.cli rotacionar-chave` até `pendentes: 0`;
4. só então remova a chave antiga da configuração e guarde-a (ou destrua-a) conforme a política de backups.
"""

import os
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.arquivos import _caminho
from app.models import Arquivo, FichaSaude, Usuario
from app.security import cifra_bytes, decifra_bytes, na_chave_atual


def _regrava(dado: bytes, contexto: str) -> tuple[bytes, bool]:
    """(dado na chave atual, se foi preciso regravar). Falha alto se nenhuma chave abre o conteúdo."""
    if na_chave_atual(dado, contexto):
        return dado, False
    return cifra_bytes(decifra_bytes(dado, contexto), contexto), True


def rotaciona(db: Session, simular: bool = False) -> dict[str, int]:
    """Regrava ficha de saúde, segredos de 2FA e arquivos. `pendentes` = o que ainda estava na chave antiga."""
    r = {"saude": 0, "segredos_2fa": 0, "arquivos": 0, "ausentes": 0}
    for f in db.scalars(select(FichaSaude)):
        dados, mudou_d = _regrava(f.dados_enc, str(f.aluno_id))
        alerta, mudou_a = (f.alerta_enc, False) if not f.alerta_enc else _regrava(f.alerta_enc, f"alerta:{f.aluno_id}")
        if mudou_d or mudou_a:
            r["saude"] += 1
            if not simular:
                f.dados_enc, f.alerta_enc = dados, alerta
    for u in db.scalars(select(Usuario).where(Usuario.totp_secret_enc.is_not(None))):
        novo, mudou = _regrava(u.totp_secret_enc, str(u.id))  # type: ignore[arg-type]
        if mudou:
            r["segredos_2fa"] += 1
            if not simular:
                u.totp_secret_enc = novo
    for a in db.scalars(select(Arquivo)):
        caminho = _caminho(a.escola_id, a.id)
        try:
            bruto = caminho.read_bytes()
        except FileNotFoundError:
            r["ausentes"] += 1
            continue
        novo, mudou = _regrava(bruto, f"arquivo:{a.id}")
        if mudou:
            r["arquivos"] += 1
            if not simular:
                _grava_atomico(caminho, novo)
    r["pendentes"] = r["saude"] + r["segredos_2fa"] + r["arquivos"] if simular else 0
    return r


def _grava_atomico(destino: Path, dado: bytes) -> None:
    tmp = destino.with_suffix(".tmp")
    tmp.write_bytes(dado)
    os.chmod(tmp, 0o600)
    tmp.replace(destino)


_ = uuid  # (ids chegam como UUID do ORM; import mantido para tipagem futura)
