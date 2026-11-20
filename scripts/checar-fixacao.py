#!/usr/bin/env python3
"""Confere que tudo que vem de fora está fixado (cadeia de suprimentos, MO.1).

- Toda Action do GitHub usa o SHA completo do commit (40 caracteres), com a versão num comentário.
- Toda imagem Docker (FROM, image: e as usadas em comandos da CI) tem tag e digest sha256.
- A mesma imagem tem o mesmo digest em todo lugar: o Postgres da CI e do desenvolvimento é o da produção,
  e o Caddy que valida o Caddyfile na CI é o da imagem do site.

O Dependabot atualiza os digests e os SHAs; este script garante que nada novo entre sem fixação e que uma
atualização não deixe um arquivo para trás.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
DOCKERFILES = sorted((RAIZ / "deploy").glob("Dockerfile*"))
COMPOSES = [RAIZ / "infra" / "docker-compose.yml", RAIZ / "deploy" / "docker-compose.prod.yml"]

USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)(.*)$", re.MULTILINE)
IMAGEM = re.compile(r"(?:^\s*FROM\s+|^\s*image:\s*)(\S+)", re.MULTILINE)
# imagens chamadas direto em comandos (docker run ... imagem:tag@sha256:...)
IMAGEM_EM_COMANDO = re.compile(r"\b([a-z0-9./-]+:[\w.-]+(?:@sha256:[0-9a-f]{64})?)\s+caddy\b")
FIXADA = re.compile(r"^[a-z0-9./-]+:[\w.-]+@sha256:[0-9a-f]{64}$")


def main() -> int:
    erros: list[str] = []
    digests: dict[str, set[tuple[str, str]]] = {}

    for wf in WORKFLOWS:
        texto = wf.read_text()
        for m in USES.finditer(texto):
            ref, resto = m.group(1), m.group(2)
            if ref.startswith("./"):
                continue
            if not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", ref):
                erros.append(f"{wf.relative_to(RAIZ)}: Action sem SHA completo: {ref}")
            elif "#" not in resto:
                erros.append(f"{wf.relative_to(RAIZ)}: Action sem a versão em comentário: {ref}")

    def registra(arquivo: Path, img: str) -> None:
        if not FIXADA.match(img):
            erros.append(f"{arquivo.relative_to(RAIZ)}: imagem sem tag e digest: {img}")
            return
        nome, _digest = img.split("@")
        digests.setdefault(nome.rsplit(":", 1)[0], set()).add((img, str(arquivo.relative_to(RAIZ))))

    for arq in [*DOCKERFILES, *COMPOSES, *WORKFLOWS]:
        texto = arq.read_text()
        for m in IMAGEM.finditer(texto):
            registra(arq, m.group(1))
        if arq in WORKFLOWS:
            for m in IMAGEM_EM_COMANDO.finditer(texto):
                registra(arq, m.group(1))

    for nome, usos in sorted(digests.items()):
        if len({img for img, _ in usos}) > 1:
            lista = "; ".join(f"{arq}: {img}" for img, arq in sorted(usos, key=lambda u: u[1]))
            erros.append(f"{nome} com versões diferentes entre arquivos: {lista}")

    for nome in ("postgres", "caddy"):
        if nome not in digests:
            erros.append(f"imagem {nome} não encontrada (o script precisa ser atualizado?)")

    if erros:
        print("Fixação da cadeia de suprimentos com problemas:", *erros, sep="\n- ")
        return 1
    print(f"ok: Actions fixadas por SHA e {len(digests)} imagens fixadas por digest, iguais em todos os arquivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
