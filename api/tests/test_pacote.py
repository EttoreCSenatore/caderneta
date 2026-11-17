"""Pacote para revisão jurídica: o gerador monta o documento único e o modelo de instalação cobre os campos."""

import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "scripts" / "gerar-pacote-juridico.py"
EXEMPLO = RAIZ / ".lgpd" / "pacote" / "instalacao.exemplo.json"


def _gera(tmp_path, *args):
    cmd = [sys.executable, str(SCRIPT), "--saida", str(tmp_path), *args]
    return subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603 (script do próprio repositório)


def test_gera_html_e_markdown_completos_com_os_dados_da_instalacao(tmp_path):
    r = _gera(tmp_path, "--instalacao", str(EXEMPLO))
    assert r.returncode == 0, r.stderr
    assert r.stderr == ""  # o exemplo preenche todos os campos
    md = (tmp_path / "pacote-juridico.md").read_text(encoding="utf-8")
    html = (tmp_path / "pacote-juridico.html").read_text(encoding="utf-8")
    assert "{{" not in md and "{{" not in html
    assert "Colégio Exemplo" in md and "Tecnologia Exemplo Ltda." in md
    for trecho in (
        "P1. Enquadramento",
        "P14. Software livre",
        "Anexo A",
        "Política de privacidade",
        "Termos de uso",
        "ROPA",
        "RIPD",
        "LIA",
        "Plano de resposta a incidentes",
        "Modelo de parecer",
    ):
        assert trecho in md, trecho
    assert "<nav>" in html and 'id="anexo-g"' in html and "<table>" in html


def test_sem_dados_da_instalacao_avisa_o_que_falta_mas_gera(tmp_path):
    r = _gera(tmp_path)
    assert r.returncode == 0
    assert "Campos a preencher" in r.stderr and "escola_nome" in r.stderr
    assert "[A PREENCHER: escola_nome]" in (tmp_path / "pacote-juridico.md").read_text(encoding="utf-8")


def test_exemplo_cobre_todos_os_campos_dos_modelos():
    usados = set()
    for f in (RAIZ / ".lgpd" / "pacote").glob("0*.md"):
        usados |= set(re.findall(r"\{\{(\w+)\}\}", f.read_text(encoding="utf-8")))
    exemplo = set(json.loads(EXEMPLO.read_text(encoding="utf-8")))
    assert usados - exemplo - {"data", "versao_projeto"} == set()


def test_textos_proprios_da_instalacao_entram_no_pacote(tmp_path):
    textos = tmp_path / "textos"
    textos.mkdir()
    (textos / "termos.md").write_text(
        "---\nversao: x-1\ntitulo: T\nstatus: vigente\n---\n\n# Termos do advogado\n\nConteudo proprio.\n",
        encoding="utf-8",
    )
    dados = json.loads(EXEMPLO.read_text(encoding="utf-8")) | {"textos_legais_dir": str(textos)}
    arq = tmp_path / "inst.json"
    arq.write_text(json.dumps(dados), encoding="utf-8")
    saida = tmp_path / "saida"
    assert _gera(saida, "--instalacao", str(arq)).returncode == 0
    md = (saida / "pacote-juridico.md").read_text(encoding="utf-8")
    assert "Conteudo proprio." in md and "x-1" in md
