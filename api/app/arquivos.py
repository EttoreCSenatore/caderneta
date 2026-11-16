"""Armazenamento de arquivos (provas, trabalhos) e validação de conteúdo.

Decisão (ADR 0004): os arquivos ficam cifrados em repouso (AES-GCM, contexto = id do arquivo) em um diretório
local, atrás desta interface. Trocar por armazenamento S3 compatível (M9) só exige reescrever `grava`, `le`, `apaga`.

A validação olha o CONTEÚDO, não só a extensão: assinatura do formato, tamanho, e conteúdo ativo (JavaScript em PDF,
macros em DOCX). Não substitui um antivírus (ver `.lgpd/gaps.md`, item S1).
"""

import hashlib
import io
import os
import re
import unicodedata
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Arquivo
from app.security import cifra_bytes, decifra_bytes

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# Marcas de conteúdo ativo em PDF. Fluxos comprimidos podem escondê-las: é uma barreira, não uma garantia.
_PDF_ATIVO = re.compile(rb"/(JavaScript|JS|Launch|EmbeddedFile|RichMedia)\b")
_MAX_DOCX_DESCOMPRIMIDO = 100_000_000
_MAX_DOCX_ENTRADAS = 3000


def nome_seguro(nome: str | None) -> str:
    """Só o nome do arquivo (sem pasta), sem caracteres de controle, com no máximo 120 caracteres."""
    base = os.path.basename((nome or "").replace("\\", "/"))
    base = "".join(c for c in unicodedata.normalize("NFC", base) if c.isprintable() and c not in '<>:"|?*')
    return base.strip(" .")[:120] or "arquivo"


def valida(nome: str | None, dados: bytes) -> tuple[str, str]:
    """Devolve (nome limpo, tipo MIME) ou levanta 422/413."""
    limpo = nome_seguro(nome)
    if not dados:
        raise HTTPException(422, "O arquivo está vazio.")
    if len(dados) > get_settings().max_arquivo_bytes:
        mb = get_settings().max_arquivo_bytes // 1_000_000
        raise HTTPException(413, f"O arquivo passa do limite de {mb} MB.")
    ext = limpo.lower().rsplit(".", 1)[-1] if "." in limpo else ""
    if ext == "pdf":
        if not dados.startswith(b"%PDF-"):
            raise HTTPException(422, "O arquivo não é um PDF válido.")
        if _PDF_ATIVO.search(dados):
            raise HTTPException(
                422, "O PDF contém conteúdo ativo (scripts ou anexos) e não é aceito. Exporte-o novamente."
            )
        return limpo, PDF
    if ext == "docx":
        _valida_docx(dados)
        return limpo, DOCX
    raise HTTPException(422, "Envie um arquivo PDF ou DOCX.")


def _valida_docx(dados: bytes) -> None:
    if not dados.startswith(b"PK\x03\x04") or not zipfile.is_zipfile(io.BytesIO(dados)):
        raise HTTPException(422, "O arquivo não é um DOCX válido.")
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            infos = z.infolist()
            nomes = {i.filename for i in infos}
            if len(infos) > _MAX_DOCX_ENTRADAS or sum(i.file_size for i in infos) > _MAX_DOCX_DESCOMPRIMIDO:
                raise HTTPException(422, "O DOCX é grande demais depois de descompactado.")
            if any(n.startswith(("/", "..")) or "/../" in n for n in nomes):
                raise HTTPException(422, "O DOCX tem caminhos inválidos.")
            if "[Content_Types].xml" not in nomes or "word/document.xml" not in nomes:
                raise HTTPException(422, "O arquivo não é um DOCX válido.")
            if any(n.lower().endswith(("vbaproject.bin", ".exe", ".dll")) for n in nomes):
                raise HTTPException(422, "O DOCX contém macros ou programas e não é aceito.")
    except zipfile.BadZipFile:
        raise HTTPException(422, "O arquivo não é um DOCX válido.") from None


def _caminho(escola_id: uuid.UUID, arquivo_id: uuid.UUID) -> Path:
    return Path(get_settings().storage_dir) / str(escola_id) / f"{arquivo_id}.bin"


def grava(db: Session, *, escola_id: uuid.UUID, usuario_id: uuid.UUID, nome: str | None, dados: bytes) -> Arquivo:
    limpo, mime = valida(nome, dados)
    a = Arquivo(
        id=uuid.uuid4(),
        escola_id=escola_id,
        nome=limpo,
        mime=mime,
        tamanho=len(dados),
        sha256=hashlib.sha256(dados).hexdigest(),
        criado_por=usuario_id,
    )
    destino = _caminho(escola_id, a.id)
    destino.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = destino.with_suffix(".tmp")
    tmp.write_bytes(cifra_bytes(dados, f"arquivo:{a.id}"))
    os.chmod(tmp, 0o600)
    tmp.replace(destino)
    db.add(a)
    db.flush()
    return a


def le(a: Arquivo) -> bytes:
    try:
        return decifra_bytes(_caminho(a.escola_id, a.id).read_bytes(), f"arquivo:{a.id}")
    except FileNotFoundError:
        raise HTTPException(410, "O arquivo não está mais disponível.") from None


def apaga(a: Arquivo) -> None:
    _caminho(a.escola_id, a.id).unlink(missing_ok=True)
