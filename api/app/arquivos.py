"""Armazenamento de arquivos (provas, trabalhos, anexos) e validação de conteúdo.

Decisão (ADR 0004): os arquivos ficam cifrados em repouso (AES-GCM, contexto = id do arquivo) em um diretório
local, atrás desta interface. Trocar por armazenamento S3 compatível (M9) só exige reescrever `grava`, `le`, `apaga`.

Todo upload passa por: validação do CONTEÚDO (assinatura, tamanho, conteúdo ativo), antivírus (ClamAV, falha fechada),
limpeza de metadados de imagem (EXIF com localização, por exemplo) e, para DOCX, conversão para PDF (conversor ligado).
"""

import hashlib
import io
import os
import re
import struct
import unicodedata
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import antivirus, conversor
from app.config import get_settings
from app.models import Arquivo
from app.security import cifra_bytes, decifra_bytes

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
JPEG = "image/jpeg"
PNG = "image/png"
TIPOS_PEDIDO = ("pdf", "docx")
TIPOS_ANEXO = ("pdf", "jpg", "jpeg", "png")
# Marcas de conteúdo ativo em PDF. Fluxos comprimidos podem escondê-las: é uma barreira, não uma garantia.
_PDF_ATIVO = re.compile(rb"/(JavaScript|JS|Launch|EmbeddedFile|RichMedia)\b")
_MAX_DOCX_DESCOMPRIMIDO = 100_000_000
_MAX_DOCX_ENTRADAS = 3000


def nome_seguro(nome: str | None) -> str:
    """Só o nome do arquivo (sem pasta), sem caracteres de controle, com no máximo 120 caracteres."""
    base = os.path.basename((nome or "").replace("\\", "/"))
    base = "".join(c for c in unicodedata.normalize("NFC", base) if c.isprintable() and c not in '<>:"|?*')
    return base.strip(" .")[:120] or "arquivo"


def valida(
    nome: str | None, dados: bytes, permitidos: tuple[str, ...] = TIPOS_PEDIDO, limite: int | None = None
) -> tuple[str, str]:
    """Devolve (nome limpo, tipo MIME) ou levanta 422/413."""
    limpo = nome_seguro(nome)
    if not dados:
        raise HTTPException(422, "O arquivo está vazio.")
    maximo = limite or get_settings().max_arquivo_bytes
    if len(dados) > maximo:
        raise HTTPException(413, f"O arquivo passa do limite de {maximo // 1_000_000} MB.")
    ext = limpo.lower().rsplit(".", 1)[-1] if "." in limpo else ""
    if ext not in permitidos:
        raise HTTPException(422, "Envie um arquivo " + ("PDF ou DOCX." if "docx" in permitidos else "PDF, JPG ou PNG."))
    if ext == "pdf":
        if not dados.startswith(b"%PDF-"):
            raise HTTPException(422, "O arquivo não é um PDF válido.")
        if _PDF_ATIVO.search(dados):
            raise HTTPException(422, "O PDF tem conteúdo ativo (scripts ou anexos) e não é aceito. Exporte-o de novo.")
        return limpo, PDF
    if ext == "docx":
        _valida_docx(dados)
        return limpo, DOCX
    if ext in ("jpg", "jpeg"):
        return limpo, JPEG
    return limpo, PNG


def limpa_metadados(mime: str, dados: bytes) -> bytes:
    """Remove EXIF, XMP, comentários e datas das imagens (podem trazer localização e o aparelho). Valida a estrutura."""
    if mime == JPEG:
        return _limpa_jpeg(dados)
    if mime == PNG:
        return _limpa_png(dados)
    return dados


def _limpa_jpeg(d: bytes) -> bytes:
    if not d.startswith(b"\xff\xd8"):
        raise HTTPException(422, "O arquivo não é um JPEG válido.")
    out, i = bytearray(d[:2]), 2
    while i + 4 <= len(d):
        if d[i] != 0xFF:
            raise HTTPException(422, "O arquivo não é um JPEG válido.")
        marca = d[i + 1]
        if marca == 0xFF:  # preenchimento
            i += 1
            continue
        if marca == 0xDA:  # início dos dados da imagem: o resto vai como está
            out += d[i:]
            return bytes(out)
        if marca == 0xD9:
            out += d[i : i + 2]
            return bytes(out)
        tam = struct.unpack(">H", d[i + 2 : i + 4])[0]
        if tam < 2 or i + 2 + tam > len(d):
            raise HTTPException(422, "O arquivo não é um JPEG válido.")
        if marca not in (0xE1, 0xED, 0xFE):  # descarta APP1 (Exif/XMP), APP13 e comentários
            out += d[i : i + 2 + tam]
        i += 2 + tam
    raise HTTPException(422, "O arquivo não é um JPEG válido.")


_PNG_DESCARTA = {b"eXIf", b"tEXt", b"zTXt", b"iTXt", b"tIME"}


def _limpa_png(d: bytes) -> bytes:
    if not d.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(422, "O arquivo não é um PNG válido.")
    out, i, viu_iend = bytearray(d[:8]), 8, False
    while i + 12 <= len(d):
        tam = struct.unpack(">I", d[i : i + 4])[0]
        tipo = d[i + 4 : i + 8]
        fim = i + 12 + tam
        if fim > len(d):
            break
        if tipo not in _PNG_DESCARTA:
            out += d[i:fim]
        i = fim
        if tipo == b"IEND":
            viu_iend = True
            break
    if not viu_iend or not out[8:].startswith(struct.pack(">I", 13) + b"IHDR"):
        raise HTTPException(422, "O arquivo não é um PNG válido.")
    return bytes(out)


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


def prepara(
    nome: str | None, dados: bytes, permitidos: tuple[str, ...] = TIPOS_PEDIDO, limite: int | None = None
) -> tuple[str, str, bytes]:
    """Validação, antivírus, limpeza de imagem e conversão. Devolve (nome, mime, bytes) prontos para guardar."""
    limpo, mime = valida(nome, dados, permitidos, limite)
    antivirus.verifica(dados)
    dados = limpa_metadados(mime, dados)
    if mime == DOCX and get_settings().conversor == "libreoffice":
        pdf = conversor.docx_para_pdf(dados)
        _, mime = valida("saida.pdf", pdf)  # o resultado também precisa passar na validação de PDF
        dados = pdf
        limpo = (limpo.rsplit(".", 1)[0] or "arquivo")[:116] + ".pdf"
    return limpo, mime, dados


def grava(
    db: Session,
    *,
    escola_id: uuid.UUID,
    usuario_id: uuid.UUID,
    nome: str | None,
    dados: bytes,
    permitidos: tuple[str, ...] = TIPOS_PEDIDO,
    limite: int | None = None,
) -> Arquivo:
    limpo, mime, dados = prepara(nome, dados, permitidos, limite)
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
