"""M6.3: histórico escolar em PDF (gerador mínimo, emissão registrada e conferência pública do código)."""

import re

import pytest
from sqlalchemy import text

from app.pdfmin import Documento, largura, quebra
from tests.conftest import Cliente


def _tem_xref_valido(pdf: bytes) -> bool:
    """Confere que o startxref aponta para a tabela e que cada deslocamento cai no início de 'N 0 obj'."""
    inicio = int(re.search(rb"startxref\n(\d+)\n%%EOF", pdf).group(1))
    assert pdf[inicio : inicio + 4] == b"xref"
    n = int(pdf[inicio:].split(b"\n")[1].split()[1])
    entradas = pdf[inicio:].split(b"\n")[3 : 3 + n - 1]
    for i, e in enumerate(entradas, 1):
        off = int(e.split()[0])
        assert pdf[off:].startswith(b"%d 0 obj" % i)
    return True


def test_pdfmin_estrutura_paginas_e_texto():
    d = Documento("Teste", "rodape")
    for i in range(120):
        d.paragrafo(f"Linha {i} com acentuação: ação, ônibus, coração (parênteses) e \\ barra", 10)
    pdf = d.bytes()
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
    assert _tem_xref_valido(pdf)
    paginas = len(re.findall(rb"/Type /Page /", pdf))
    assert paginas >= 3 and f"Página {paginas} de {paginas}".encode("cp1252") in pdf
    assert b"a\xe7\xe3o" in pdf and b"\\(par\xeanteses\\)" in pdf and b"\\\\ barra" in pdf  # cp1252 e escapes


def test_quebra_de_linha_e_palavra_gigante():
    linhas = quebra("uma frase comum que precisa quebrar em varias linhas curtas", 120, 10)
    assert len(linhas) > 1 and all(largura(x, 10) <= 120 for x in linhas)
    gigante = quebra("X" * 200, 100, 10)
    assert len(gigante) > 1 and all(largura(x, 10) <= 100 for x in gigante)
    assert quebra("a\n\nb", 100, 10) == ["a", "", "b"]


def test_tabela_repete_cabecalho_ao_virar_pagina():
    d = Documento("T")
    d.tabela([("Coluna", 200, "e"), ("Valor", 100, "d")], [[f"item {i}", str(i)] for i in range(120)])
    pdf = d.bytes()
    assert pdf.count(b"(Coluna)") >= 2 and _tem_xref_valido(pdf)


@pytest.fixture
def com_notas(mundo, entrar, owner_engine):
    a, _ = mundo
    with owner_engine.begin() as db:
        atrib = str(db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar())
    prof = entrar("prof.a@teste.com")
    d = prof.get(f"/api/atribuicoes/{atrib}/diario").json()
    mat = {x["nome"].split()[0]: x["matricula_id"] for x in d["alunos"]}
    av = prof.post(
        f"/api/atribuicoes/{atrib}/avaliacoes", json={"periodo_id": d["periodos"][0]["id"], "nome": "P1", "peso": 1}
    ).json()["id"]
    prof.put(f"/api/avaliacoes/{av}/notas", json={"notas": [{"matricula_id": mat["João"], "valor": 7.5}]})
    return a


def _emitir(c, aluno):
    return c.post(f"/api/alunos/{aluno.id}/historico-escolar")


def test_emissao_conteudo_e_registro(com_notas, entrar, owner_engine):
    a = com_notas
    coord = entrar("coord.a@teste.com")
    # dados que NÃO podem sair no PDF
    entrar("prof.a@teste.com").post(
        f"/api/alunos/{a.alunos['joao'].id}/anotacoes", json={"tipo": "pedagogica", "corpo": "SEGREDO-DA-ANOTACAO"}
    )
    r = _emitir(coord, a.alunos["joao"])
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert 'filename="historico-escolar-joao-silva-a.pdf"' in r.headers["content-disposition"]
    pdf = r.content
    assert _tem_xref_valido(pdf)
    assert "HISTÓRICO ESCOLAR".encode("cp1252") in pdf and b"Escola A" in pdf
    assert "Jo\u00e3o Silva A".encode("cp1252") in pdf and b"01/05/2013" in pdf
    assert "Matem\u00e1tica".encode("cp1252") in pdf and b"2026" in pdf and b"7,5" in pdf
    assert b"7\xba A" in pdf  # 7º A
    assert b"SEGREDO" not in pdf and b"cpf" not in pdf.lower()
    codigo = re.search(rb"C\xf3digo de verifica\xe7\xe3o ([0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4})", pdf).group(1).decode()
    with owner_engine.begin() as db:
        h = db.execute(text("SELECT codigo, resumo_sha256 FROM historico_emitido")).one()
        n = db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'historico.emitir'")).scalar()
    assert h.codigo == codigo and len(h.resumo_sha256) == 64 and n == 1
    lista = coord.get(f"/api/alunos/{a.alunos['joao'].id}/historicos-emitidos").json()
    assert [x["codigo"] for x in lista] == [codigo] and lista[0]["emitido_por"] == "Coord.A"
    outro = re.search(rb"verifica\xe7\xe3o ([0-9A-F-]{14})", _emitir(coord, a.alunos["joao"]).content).group(1).decode()
    assert outro != codigo  # cada emissão tem o seu código


def test_quem_pode_emitir(com_notas, entrar):
    a = com_notas
    joao = a.alunos["joao"]
    for quem in ("prof.a@teste.com", "mae.a@teste.com", "aluno.a@teste.com"):
        assert _emitir(entrar(quem), joao).status_code == 403
        assert entrar(quem).get(f"/api/alunos/{joao.id}/historicos-emitidos").status_code == 403
    assert _emitir(entrar("admin.a@teste.com"), joao).status_code == 200
    assert _emitir(entrar("coord.b@teste.com"), joao).status_code == 404  # outra escola


def test_verificacao_publica_minima(com_notas, entrar):
    a = com_notas
    pdf = _emitir(entrar("coord.a@teste.com"), a.alunos["joao"]).content
    codigo = re.search(rb"verifica\xe7\xe3o ([0-9A-F-]{14})", pdf).group(1).decode()
    anonimo = Cliente()
    r = anonimo.get(f"/api/historico/verificar/{codigo}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["valido"] is True and corpo["escola"] == "Escola A" and corpo["aluno"] == "J. S."
    assert set(corpo) == {"valido", "escola", "emitido_em", "aluno"}  # sem nome completo, nascimento ou notas
    assert anonimo.get(f"/api/historico/verificar/{codigo.lower().replace('-', '')}").status_code == 200
    for ruim in ("0000-0000-0000", "lixo", "A" * 40, "FFFF-FFFF-FFFF"):
        assert anonimo.get(f"/api/historico/verificar/{ruim}").status_code == 404


def test_pdf_com_varios_anos_e_sem_matricula(mundo, entrar):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    r = _emitir(coord, a.alunos["maria"])
    assert r.status_code == 200 and b"Maria Silva A" in r.content
    assert _tem_xref_valido(r.content)
