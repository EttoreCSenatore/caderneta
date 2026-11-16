"""M5: provas, trabalhos e fila de impressão (upload validado, fluxo, sigilo, link assinado, auditoria)."""

import io
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text

from app.config import get_settings
from tests.conftest import Cliente

PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
SEGREDO = b"GABARITO-SECRETO-123"


def pdf(extra: bytes = b"") -> bytes:
    return PDF + b"% " + extra + b"\n"


def docx(extras: dict[str, bytes] | None = None, completo: bool = True) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        if completo:
            z.writestr("word/document.xml", "<w:document/>")
        for n, d in (extras or {}).items():
            z.writestr(n, d)
    return buf.getvalue()


def dia(n: int) -> str:
    return str(datetime.now(UTC).date() + timedelta(days=n))


@pytest.fixture
def atrib(mundo, owner_engine):
    a, _ = mundo
    with owner_engine.begin() as db:
        return str(db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar())


def _novo(c, atrib, dados: bytes | None = None, nome="prova.pdf", **campos):
    form = {"titulo": "Prova bimestral", "tipo": "prova", "data_aplicacao": dia(7), "atribuicao_ids": [atrib], **campos}
    r = c.post(
        "/api/pedidos",
        data=form,
        files={"arquivo": (nome, dados if dados is not None else pdf(SEGREDO), "application/pdf")},
    )
    return r


def _id(r):
    assert r.status_code == 201, r.text
    return r.json()[0]["id"]


def _baixar(c, pid, versao="principal"):
    r = c.post(f"/api/pedidos/{pid}/arquivo-link", params={"versao": versao})
    assert r.status_code == 200, r.text
    return c.get(r.json()["url"])


# --- Validação do arquivo -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nome", "dados", "status"),
    [
        ("p.pdf", PDF, 201),
        ("p.docx", docx(), 201),
        ("p.pdf", b"isto nao e um pdf", 422),
        ("p.pdf", PDF + b"/JavaScript (app.alert(1))", 422),
        ("p.docx", docx({"word/vbaProject.bin": b"x"}), 422),
        ("p.docx", docx(completo=False), 422),
        ("p.docx", b"PK\x03\x04lixo", 422),
        ("p.exe", b"MZ", 422),
        ("p.pdf", b"", 422),
    ],
)
def test_validacao_de_conteudo(mundo, entrar, atrib, nome, dados, status):
    assert _novo(entrar("prof.a@teste.com"), atrib, dados, nome).status_code == status


def test_limite_de_tamanho(mundo, entrar, atrib, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_arquivo_bytes", 100)
    assert _novo(entrar("prof.a@teste.com"), atrib, PDF + b"x" * 200).status_code == 413


def test_nome_do_arquivo_e_limpo(mundo, entrar, atrib):
    r = _novo(entrar("prof.a@teste.com"), atrib, nome="../../etc/passwd\\..\\prova<1>.pdf")
    assert r.json()[0]["arquivo"]["nome"] == "prova1.pdf"


def test_arquivo_fica_cifrado_em_disco(mundo, entrar, atrib):
    prof = entrar("prof.a@teste.com")
    pid = _id(_novo(prof, atrib))
    brutos = [p.read_bytes() for p in Path(get_settings().storage_dir).rglob("*.bin")]
    assert brutos and all(SEGREDO not in b and b"%PDF" not in b for b in brutos)
    r = _baixar(prof, pid)
    assert r.status_code == 200 and SEGREDO in r.content and r.headers["content-type"] == "application/pdf"
    assert "attachment" in r.headers["content-disposition"]


# --- Fluxo --------------------------------------------------------------------------------------------------


def test_fluxo_completo_com_aprovacao(mundo, entrar, atrib):
    a, _ = mundo
    prof, coord, admin = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("admin.a@teste.com")
    sug = prof.get(f"/api/atribuicoes/{atrib}/copias-sugeridas").json()
    assert sug == {"alunos": 2, "reserva": 2, "total": 4}  # João e Maria na 7º A + reserva
    p = _novo(prof, atrib).json()[0]
    assert (p["status"], p["copias"], p["copias_calculadas"], p["frente_verso"]) == ("rascunho", 4, 4, True)
    pid = p["id"]
    assert prof.patch(f"/api/pedidos/{pid}", json={"copias": 30, "colorido": True}).json()["copias"] == 30
    assert prof.post(f"/api/pedidos/{pid}/aprovar").status_code == 403
    assert prof.post(f"/api/pedidos/{pid}/enviar").json()["status"] == "enviada"
    assert prof.patch(f"/api/pedidos/{pid}", json={"copias": 5}).status_code == 409  # em análise: não edita
    assert any(n["tipo"] == "impressao" for n in coord.get("/api/notificacoes").json())
    assert coord.post(f"/api/pedidos/{pid}/imprimir").status_code == 403  # só a secretaria imprime
    assert admin.post(f"/api/pedidos/{pid}/imprimir").status_code == 409  # ainda não aprovado
    assert coord.post(f"/api/pedidos/{pid}/aprovar").json()["status"] == "aprovada"
    assert coord.post(f"/api/pedidos/{pid}/aprovar").status_code == 409
    fila = admin.get("/api/pedidos", params={"status": "aprovada", "de": dia(0), "ate": dia(30)}).json()
    assert [x["id"] for x in fila] == [pid]
    assert admin.patch(f"/api/pedidos/{pid}", json={"copias": 32}).json()["copias"] == 32  # secretaria ajusta
    assert admin.post(f"/api/pedidos/{pid}/imprimir").json()["status"] == "impressa"
    assert prof.get("/api/notificacoes").json()[0]["titulo"] == "Seu material foi impresso"
    assert admin.patch(f"/api/pedidos/{pid}", json={"copias": 1}).status_code == 409
    assert admin.get("/api/pedidos", params={"de": dia(30)}).json() == []


def test_ajustes_e_reenvio(mundo, entrar, atrib):
    prof, coord = entrar("prof.a@teste.com"), entrar("coord.a@teste.com")
    pid = _id(_novo(prof, atrib))
    prof.post(f"/api/pedidos/{pid}/enviar")
    assert coord.post(f"/api/pedidos/{pid}/ajustes", json={"corpo": ""}).status_code == 422
    r = coord.post(f"/api/pedidos/{pid}/ajustes", json={"corpo": "Faltou a questão 5."}).json()
    assert r["status"] == "ajustes" and r["comentarios"][0]["corpo"] == "Faltou a questão 5."
    antigos = len(list(Path(get_settings().storage_dir).rglob("*.bin")))
    nova = prof.post(
        f"/api/pedidos/{pid}/arquivo", data={"versao": "principal"}, files={"arquivo": ("v2.pdf", pdf(b"v2"), "x")}
    )
    assert nova.status_code == 200 and nova.json()["arquivo"]["nome"] == "v2.pdf"
    assert len(list(Path(get_settings().storage_dir).rglob("*.bin"))) == antigos  # o arquivo antigo foi apagado
    assert prof.post(f"/api/pedidos/{pid}/comentarios", json={"corpo": "Corrigido."}).status_code == 201
    assert prof.post(f"/api/pedidos/{pid}/enviar").json()["status"] == "enviada"


def test_antecedencia_minima(mundo, entrar, atrib):
    prof, admin = entrar("prof.a@teste.com"), entrar("admin.a@teste.com")
    cfg = admin.get("/api/impressao/config").json()
    assert cfg == {"aprovacao": True, "reserva_copias": 2, "antecedencia_dias": 2}
    pid = _id(_novo(prof, atrib, data_aplicacao=dia(1)))
    assert prof.get(f"/api/pedidos/{pid}").json()["atrasado"] is True
    r = prof.post(f"/api/pedidos/{pid}/enviar")
    assert r.status_code == 409 and "2 dia(s)" in r.json()["detail"]
    assert admin.post(f"/api/pedidos/{pid}/enviar").status_code == 200  # a direção pode abrir exceção
    assert _novo(prof, atrib, data_aplicacao=dia(-1)).status_code == 422
    assert prof.put("/api/impressao/config", json=cfg).status_code == 403
    novo = admin.put(
        "/api/impressao/config", json={"aprovacao": True, "reserva_copias": 3, "antecedencia_dias": 0}
    ).json()
    assert novo["antecedencia_dias"] == 0
    assert prof.get(f"/api/atribuicoes/{atrib}/copias-sugeridas").json()["total"] == 5


def test_sem_aprovacao_vai_direto_para_a_fila(mundo, entrar, atrib):
    prof, admin = entrar("prof.a@teste.com"), entrar("admin.a@teste.com")
    admin.put("/api/impressao/config", json={"aprovacao": False, "reserva_copias": 2, "antecedencia_dias": 2})
    pid = _id(_novo(prof, atrib))
    assert prof.post(f"/api/pedidos/{pid}/enviar").json()["status"] == "aprovada"
    assert any(n["tipo"] == "impressao" for n in admin.get("/api/notificacoes").json())


def test_adaptada_e_exclusao_de_rascunho(mundo, entrar, atrib):
    prof = entrar("prof.a@teste.com")
    form = {
        "titulo": "Prova",
        "tipo": "prova",
        "data_aplicacao": dia(7),
        "atribuicao_ids": [atrib],
        "copias_adaptadas": 2,
    }
    r = prof.post(
        "/api/pedidos",
        data=form,
        files={"arquivo": ("a.pdf", pdf(b"a"), "x"), "arquivo_adaptado": ("fonte-grande.pdf", pdf(b"g"), "x")},
    ).json()[0]
    assert r["copias_adaptadas"] == 2 and r["adaptado"]["nome"] == "fonte-grande.pdf"
    assert _baixar(prof, r["id"], "adaptado").status_code == 200
    antes = len(list(Path(get_settings().storage_dir).rglob("*.bin")))
    assert prof.delete(f"/api/pedidos/{r['id']}").status_code == 204
    assert len(list(Path(get_settings().storage_dir).rglob("*.bin"))) == antes - 2
    pid = _id(_novo(prof, atrib))
    prof.post(f"/api/pedidos/{pid}/enviar")
    assert prof.delete(f"/api/pedidos/{pid}").status_code == 409


# --- Sigilo e download --------------------------------------------------------------------------------------


def test_sigilo_ate_publicar(mundo, entrar, atrib):
    prof, coord, admin = entrar("prof.a@teste.com"), entrar("coord.a@teste.com"), entrar("admin.a@teste.com")
    pid = _id(_novo(prof, atrib, data_aplicacao=dia(7)))
    prof.post(f"/api/pedidos/{pid}/enviar")
    coord.post(f"/api/pedidos/{pid}/aprovar")
    mae, aluno = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com")
    for fora in (mae, aluno, entrar("prof2.a@teste.com"), entrar("mae.b@teste.com"), entrar("coord.b@teste.com")):
        assert fora.get(f"/api/pedidos/{pid}").status_code == 404
        assert fora.post(f"/api/pedidos/{pid}/arquivo-link").status_code in (403, 404)
    assert mae.get("/api/pedidos").json() == []
    assert prof.post(f"/api/pedidos/{pid}/publicar", json={"publicado": True}).status_code == 409  # antes da aplicação
    assert admin.get(f"/api/pedidos/{pid}").status_code == 200
    assert _baixar(coord, pid).status_code == 200 and _baixar(admin, pid).status_code == 200


def test_publicar_trabalho_para_a_turma(mundo, entrar, atrib):
    prof, coord = entrar("prof.a@teste.com"), entrar("coord.a@teste.com")
    pid = _id(_novo(prof, atrib, titulo="Trabalho de frações", tipo="trabalho", data_aplicacao=dia(10)))
    assert prof.post(f"/api/pedidos/{pid}/publicar", json={"publicado": True}).status_code == 409  # ainda rascunho
    prof.post(f"/api/pedidos/{pid}/enviar")
    coord.post(f"/api/pedidos/{pid}/aprovar")
    assert prof.post(f"/api/pedidos/{pid}/publicar", json={"publicado": True}).json()["publicado"] is True
    mae = entrar("mae.a@teste.com")
    (item,) = mae.get("/api/pedidos").json()
    assert item["titulo"] == "Trabalho de frações" and "copias" not in item  # família não vê dados internos
    assert _baixar(mae, pid).status_code == 200
    assert mae.post(f"/api/pedidos/{pid}/arquivo-link", params={"versao": "adaptado"}).status_code == 404
    assert mae.patch(f"/api/pedidos/{pid}", json={"copias": 1}).status_code == 404
    assert [n["tipo"] for n in mae.get("/api/notificacoes").json()][0] == "material"
    cal = mae.get("/api/calendario", params={"inicio": dia(0), "fim": dia(30)}).json()
    assert any(i["origem"] == "trabalho" and i["inicio"] == dia(10) for i in cal)
    prof.post(f"/api/pedidos/{pid}/publicar", json={"publicado": False})
    assert mae.get("/api/pedidos").json() == []
    assert mae.post(f"/api/pedidos/{pid}/arquivo-link").status_code == 404


def test_link_assinado(mundo, entrar, atrib, owner_engine, monkeypatch):
    prof, coord = entrar("prof.a@teste.com"), entrar("coord.a@teste.com")
    pid = _id(_novo(prof, atrib))
    url = prof.post(f"/api/pedidos/{pid}/arquivo-link").json()["url"]
    assert prof.get(url).status_code == 200
    assert coord.get(url).status_code == 404  # o link é de quem pediu
    assert prof.get(url[:-3] + "AAA").status_code == 404  # assinatura adulterada
    assert prof.get("/api/arquivos/lixo.lixo").status_code == 404
    assert Cliente().get(url).status_code == 401  # sem sessão
    monkeypatch.setattr(get_settings(), "link_validade_s", -1)
    vencido = prof.post(f"/api/pedidos/{pid}/arquivo-link").json()["url"]
    assert prof.get(vencido).status_code == 404
    with owner_engine.begin() as db:
        n = db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'pedido.baixar'")).scalar()
    assert n == 1  # só o download que de fato aconteceu


def test_isolamento_entre_escolas(mundo, entrar, atrib):
    pid = _id(_novo(entrar("prof.a@teste.com"), atrib))
    b = entrar("admin.b@teste.com")
    assert b.get(f"/api/pedidos/{pid}").status_code == 404
    assert b.get("/api/pedidos").json() == []
    assert b.post(f"/api/pedidos/{pid}/imprimir").status_code == 404
    assert _novo(entrar("prof.b@teste.com"), atrib).status_code == 404  # atribuição de outra escola
