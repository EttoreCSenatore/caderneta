"""Conversão de DOCX para PDF com o LibreOffice (sem interface).

O DOCX vem de um upload não confiável, então cada conversão roda num diretório temporário próprio, com perfil novo,
ambiente mínimo, limites de CPU, memória e tamanho de saída, e tempo máximo. O resultado é revalidado como PDF.
Quando o conversor está desligado, o DOCX é guardado como veio.
"""

import logging
import os
import resource
import subprocess
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app.config import get_settings

log = logging.getLogger("caderneta.conversor")
_ERRO = "Não foi possível converter o DOCX para PDF. Exporte como PDF no seu editor e envie de novo."


def _limites() -> None:  # roda no processo filho, antes do exec
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (100_000_000, 100_000_000))


def docx_para_pdf(dados: bytes) -> bytes:
    s = get_settings()
    with tempfile.TemporaryDirectory(prefix="caderneta-conv-") as tmp:
        base = Path(tmp)
        entrada, saida, perfil = base / "entrada.docx", base / "saida", base / "perfil"
        saida.mkdir()
        entrada.write_bytes(dados)
        cmd = [
            s.soffice_path,
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--nodefault",
            "--nologo",
            f"-env:UserInstallation=file://{perfil}",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            str(saida),
            str(entrada),
        ]
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(base), "LANG": "C.UTF-8"}
        try:
            r = subprocess.run(  # noqa: S603 - comando fixo, sem shell e sem entrada do usuário
                cmd,
                env=env,
                cwd=tmp,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=s.conversor_timeout_s,
                preexec_fn=_limites,  # noqa: PLW1509
            )
        except (subprocess.TimeoutExpired, OSError):
            log.exception("falha ao executar o conversor")
            raise HTTPException(422, _ERRO) from None
        pdf = saida / "entrada.pdf"
        if r.returncode != 0 or not pdf.is_file():
            log.error("conversor retornou %s", r.returncode)
            raise HTTPException(422, _ERRO)
        return pdf.read_bytes()
