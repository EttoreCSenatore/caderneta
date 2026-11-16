"""M5 (pendências): antivírus, conversão de DOCX, anexos de mensagens, limpeza de imagens e retenção."""

import io
import os
import shutil
import socket
import struct
import threading
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import mail  # noqa: F401
from app.arquivos import limpa_metadados, valida
from app.config import get_settings
from app.notificacoes import processar
from app.retencao import elimina_vencidos, varre_orfaos

PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def jpeg(com_exif: bool = True) -> bytes:
    exif = b"Exif\0\0GPS-LAT-23.55S-LON-46.63W"
    corpo = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    if com_exif:
        corpo += b"\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif
        corpo += b"\xff\xfe\x00\x0ccomentario"
    corpo += b"\xff\xdb\x00\x04\x00\x00\xff\xda\x00\x04\x00\x00DADOS-DA-IMAGEM\xff\xd9"
    return corpo


def chunk(tipo: bytes, dados: bytes) -> bytes:
    return struct.pack(">I", len(dados)) + tipo + dados + b"\0\0\0\0"


def png(com_texto: bool = True) -> bytes:
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", b"\0" * 13)
    if com_texto:
        out += chunk(b"tEXt", b"GPS\0-23.55,-46.63") + chunk(b"eXIf", b"EXIFSECRETO")
    return out + chunk(b"IDAT", b"PIXELS") + chunk(b"IEND", b"")


# --- Limpeza de imagens -------------------------------------------------------------------------------------


def test_jpeg_perde_exif_e_comentario_mas_mantem_a_imagem():
    limpo = limpa_metadados("image/jpeg", jpeg())
    assert b"GPS" not in limpo and b"Exif" not in limpo and b"comentario" not in limpo
    assert b"JFIF" in limpo and b"DADOS-DA-IMAGEM" in limpo and limpo.endswith(b"\xff\xd9")
    assert limpa_metadados("image/jpeg", jpeg(False)) == jpeg(False)


def test_png_perde_texto_e_exif_mas_mantem_a_imagem():
    limpo = limpa_metadados("image/png", png())
    assert b"GPS" not in limpo and b"EXIFSECRETO" not in limpo
    assert limpo == png(False)


@pytest.mark.parametrize(("mime", "dados"), [("image/jpeg", b"nao e jpeg"), ("image/png", b"\x89PNG\r\n\x1a\nlixo")])
def test_imagem_malformada_e_recusada(mime, dados):
    with pytest.raises(Exception, match="422|válido"):
        limpa_metadados(mime, dados)


def test_tipos_permitidos_por_uso():
    assert valida("a.png", png(), ("pdf", "jpg", "jpeg", "png"))[1] == "image/png"
    with pytest.raises(Exception, match="PDF ou DOCX"):
        valida("a.png", png())
    with pytest.raises(Exception, match="PDF, JPG ou PNG"):
        valida("a.docx", b"x", ("pdf", "jpg", "jpeg", "png"))


# --- Antivírus (clamd falso falando o protocolo INSTREAM) -----------------------------------------------------


class ClamdFalso:
    def __init__(self, modo="ok"):
        self.modo, self.recebido = modo, []
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(5)
        self.porta = self.srv.getsockname()[1]
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        while True:
            try:
                con, _ = self.srv.accept()
            except OSError:
                return
            with con:
                dados = b""
                buf = b""
                while True:
                    pedaco = con.recv(65536)
                    if not pedaco:
                        break
                    buf += pedaco
                    if buf.startswith(b"zINSTREAM\0"):
                        resto = buf[10:]
                        dados, i = b"", 0
                        while i + 4 <= len(resto):
                            n = struct.unpack("!I", resto[i : i + 4])[0]
                            if n == 0:
                                break
                            dados += resto[i + 4 : i + 4 + n]
                            i += 4 + n
                        else:
                            continue
                        break
                self.recebido.append(dados)
                resp = {
                    "ok": b"stream: OK\0",
                    "lixo": b"alguma coisa estranha\0",
                    "erro": b"INSTREAM size limit exceeded. ERROR\0",
                }.get(self.modo)
                if self.modo == "ok" and b"EICAR" in dados:
                    resp = b"stream: Eicar-Test-Signature FOUND\0"
                if resp:
                    con.sendall(resp)

    def fecha(self):
        self.srv.close()


@pytest.fixture
def clamd(monkeypatch):
    srv = ClamdFalso()
    s = get_settings()
    monkeypatch.setattr(s, "antivirus", "clamav")
    monkeypatch.setattr(s, "clamav_host", "127.0.0.1")
    monkeypatch.setattr(s, "clamav_port", srv.porta)
    monkeypatch.setattr(s, "clamav_timeout_s", 3)
    yield srv
    srv.fecha()


def _envia_pedido(c, atrib, dados, nome="prova.pdf"):
    from tests.test_impressao import dia

    form = {"titulo": "Prova", "tipo": "prova", "data_aplicacao": dia(7), "atribuicao_ids": [atrib]}
    return c.post("/api/pedidos", data=form, files={"arquivo": (nome, dados, "application/pdf")})


@pytest.fixture
def atrib(mundo, owner_engine):
    a, _ = mundo
    with owner_engine.begin() as db:
        return str(db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar())


def test_antivirus_limpo_infectado_e_indisponivel(mundo, entrar, atrib, clamd, monkeypatch):
    prof = entrar("prof.a@teste.com")
    assert _envia_pedido(prof, atrib, PDF + b"limpo").status_code == 201
    assert clamd.recebido[-1].startswith(b"%PDF")  # o conteúdo inteiro foi enviado ao scanner
    r = _envia_pedido(prof, atrib, PDF + EICAR)
    assert r.status_code == 422 and "antivírus" in r.json()["detail"]
    clamd.modo = "lixo"
    assert _envia_pedido(prof, atrib, PDF + b"x").status_code == 503  # resposta estranha: falha fechada
    clamd.modo = "erro"
    assert _envia_pedido(prof, atrib, PDF + b"y").status_code == 503
    clamd.fecha()
    assert _envia_pedido(prof, atrib, PDF + b"z").status_code == 503  # serviço fora do ar: falha fechada
    assert len(list(Path(get_settings().storage_dir).rglob("*.bin"))) == 1  # nada foi guardado nos casos recusados


def test_producao_exige_antivirus(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("CADERNETA_ENV", "prod")
    monkeypatch.setenv("CADERNETA_DATA_KEY", "A" * 43 + "=")
    monkeypatch.setenv("CADERNETA_COOKIE_SECURE", "true")
    monkeypatch.setenv("CADERNETA_STORAGE_DIR", "/var/lib/caderneta")
    monkeypatch.setattr("app.config.Settings", Settings)
    from app.config import get_settings as gs

    gs.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="ANTIVIRUS"):
            gs()
    finally:
        monkeypatch.undo()
        gs.cache_clear()


# --- Conversão de DOCX ------------------------------------------------------------------------------------


def docx_real() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
            'wordprocessingml.document.main+xml"/></Types>',
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'officeDocument" Target="word/document.xml"/></Relationships>',
        )
        z.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Questao 1: quanto e 2 + 2?</w:t></w:r></w:p></w:body></w:document>",
        )
    return buf.getvalue()


@pytest.mark.skipif(not shutil.which("soffice"), reason="LibreOffice não instalado")
def test_docx_vira_pdf_de_verdade(mundo, entrar, atrib, monkeypatch):
    monkeypatch.setattr(get_settings(), "conversor", "libreoffice")
    prof = entrar("prof.a@teste.com")
    r = _envia_pedido(prof, atrib, docx_real(), "Prova de Matemática.docx")
    assert r.status_code == 201, r.text
    arq = r.json()[0]["arquivo"]
    assert arq["nome"] == "Prova de Matemática.pdf" and arq["mime"] == "application/pdf"
    link = prof.post(f"/api/pedidos/{r.json()[0]['id']}/arquivo-link").json()["url"]
    assert prof.get(link).content.startswith(b"%PDF-")


def test_conversor_com_falha_recusa_o_upload(mundo, entrar, atrib, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "conversor", "libreoffice")
    monkeypatch.setattr(s, "soffice_path", "/bin/false")
    r = _envia_pedido(entrar("prof.a@teste.com"), atrib, docx_real(), "p.docx")
    assert r.status_code == 422 and "converter" in r.json()["detail"]


def test_docx_sem_conversor_e_guardado_como_veio(mundo, entrar, atrib):
    r = _envia_pedido(entrar("prof.a@teste.com"), atrib, docx_real(), "p.docx")
    assert r.json()[0]["arquivo"]["nome"] == "p.docx"


# --- Anexos de mensagens ----------------------------------------------------------------------------------


def _conversa(prof, mundo_a):
    r = prof.post(
        "/api/conversas", json={"aluno_id": str(mundo_a.alunos["joao"].id), "assunto": "Atestado", "corpo": "Oi"}
    )
    return r.json()["id"]


def _anexa(c, cid, arquivos, corpo=""):
    files = [("arquivos", (n, d, "application/octet-stream")) for n, d in arquivos]
    return c.post(f"/api/conversas/{cid}/mensagens-anexos", data={"corpo": corpo}, files=files)


def test_anexos_ida_e_volta_com_exif_removido(mundo, entrar, owner_engine):
    a, _ = mundo
    prof, mae = entrar("prof.a@teste.com"), entrar("mae.a@teste.com")
    cid = _conversa(prof, a)
    r = _anexa(mae, cid, [("atestado.jpg", jpeg()), ("laudo.pdf", PDF)], "Segue o atestado.")
    assert r.status_code == 201, r.text
    assert [x["nome"] for x in r.json()["anexos"]] == ["atestado.jpg", "laudo.pdf"]
    d = prof.get(f"/api/conversas/{cid}").json()
    msg = d["mensagens"][-1]
    assert msg["corpo"] == "Segue o atestado." and len(msg["anexos"]) == 2
    foto = next(x for x in msg["anexos"] if x["nome"] == "atestado.jpg")
    url = prof.post(f"/api/conversas/{cid}/anexos/{foto['id']}/link").json()["url"]
    baixado = prof.get(url)
    assert baixado.status_code == 200 and baixado.headers["content-type"] == "image/jpeg"
    assert b"GPS" not in baixado.content and b"DADOS-DA-IMAGEM" in baixado.content
    assert any(n["tipo"] == "mensagem" for n in prof.get("/api/notificacoes").json())
    with owner_engine.begin() as db:
        n = db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'mensagem.baixar'")).scalar()
    assert n == 1


def test_anexo_so_sem_texto_e_previa(mundo, entrar):
    a, _ = mundo
    prof, mae = entrar("prof.a@teste.com"), entrar("mae.a@teste.com")
    cid = _conversa(prof, a)
    assert _anexa(mae, cid, [("a.png", png())]).status_code == 201
    assert mae.get("/api/conversas").json()[0]["previa"] == "(1 anexo)"


@pytest.mark.parametrize(
    ("arquivos", "status"),
    [
        ([("a.pdf", PDF)] * 4, 422),  # no máximo 3
        ([("a.docx", b"PK\x03\x04")], 422),  # DOCX não vale em mensagem
        ([("a.exe", b"MZ")], 422),
        ([("a.jpg", b"nao e jpeg")], 422),
        ([], 422),
    ],
)
def test_anexos_invalidos(mundo, entrar, arquivos, status):
    a, _ = mundo
    prof = entrar("prof.a@teste.com")
    cid = _conversa(prof, a)
    assert _anexa(prof, cid, arquivos).status_code == status


def test_limite_de_tamanho_do_anexo(mundo, entrar, monkeypatch):
    a, _ = mundo
    monkeypatch.setattr(get_settings(), "max_anexo_bytes", 100)
    prof = entrar("prof.a@teste.com")
    assert _anexa(prof, _conversa(prof, a), [("a.pdf", PDF + b"x" * 200)]).status_code == 413


def test_anexo_so_para_quem_participa(mundo, entrar):
    a, _ = mundo
    prof, mae = entrar("prof.a@teste.com"), entrar("mae.a@teste.com")
    cid = _conversa(prof, a)
    _anexa(mae, cid, [("laudo.pdf", PDF)])
    aid = prof.get(f"/api/conversas/{cid}").json()["mensagens"][-1]["anexos"][0]["id"]
    for fora in (entrar("prof2.a@teste.com"), entrar("aluno.a@teste.com"), entrar("mae.b@teste.com")):
        assert fora.post(f"/api/conversas/{cid}/anexos/{aid}/link").status_code == 404
        assert _anexa(fora, cid, [("x.pdf", PDF)]).status_code == 404
    url = prof.post(f"/api/conversas/{cid}/anexos/{aid}/link").json()["url"]
    assert mae.get(url).status_code == 404  # o link é de quem pediu
    assert entrar("coord.a@teste.com").post(f"/api/conversas/{cid}/anexos/{aid}/link").status_code == 200  # supervisão
    assert prof.post(f"/api/conversas/{cid}/anexos/00000000-0000-0000-0000-000000000000/link").status_code == 404


# --- Retenção ---------------------------------------------------------------------------------------------


def _bins() -> set[Path]:
    return set(Path(get_settings().storage_dir).rglob("*.bin"))


def test_retencao_elimina_pedidos_rascunhos_e_anexos(mundo, entrar, atrib, owner_engine):
    a, _ = mundo
    prof, mae = entrar("prof.a@teste.com"), entrar("mae.a@teste.com")
    antes = _bins()
    velho = _envia_pedido(prof, atrib, PDF + b"velho").json()[0]["id"]
    rascunho = _envia_pedido(prof, atrib, PDF + b"rascunho").json()[0]["id"]
    recente = _envia_pedido(prof, atrib, PDF + b"recente").json()[0]["id"]
    cid = _conversa(prof, a)
    _anexa(mae, cid, [("atestado.pdf", PDF + b"anexo")], "texto fica")
    assert len(_bins() - antes) == 4
    with owner_engine.begin() as db:
        db.execute(text("UPDATE pedido_impressao SET data_aplicacao = current_date - 400 WHERE id = :i"), {"i": velho})
        db.execute(
            text("UPDATE pedido_impressao SET criado_em = now() - interval '100 days' WHERE id = :i"), {"i": rascunho}
        )
        db.execute(text("UPDATE mensagem_anexo SET criado_em = now() - interval '400 days'"))
    with Session(owner_engine) as db, db.begin():
        r = elimina_vencidos(db)
        n = db.execute(text("SELECT count(*) FROM auditoria WHERE acao = 'retencao.eliminar'")).scalar()
    assert (r["pedidos"], r["anexos"]) == (2, 1) and n == 2
    assert len(_bins() - antes) == 1  # só o pedido recente continua no disco
    assert (
        prof.get(f"/api/pedidos/{velho}").status_code == 404 and prof.get(f"/api/pedidos/{recente}").status_code == 200
    )
    d = prof.get(f"/api/conversas/{cid}").json()
    assert d["mensagens"][-1]["corpo"] == "texto fica" and d["mensagens"][-1]["anexos"] == []


def test_retencao_nao_apaga_arquivo_compartilhado_ainda_em_uso(mundo, entrar, atrib, owner_engine):
    prof = entrar("prof.a@teste.com")
    antes = _bins()
    r = _envia_pedido(prof, atrib, PDF + b"compartilhado")
    pid = r.json()[0]["id"]
    with owner_engine.begin() as db:  # um segundo pedido usando o mesmo arquivo, ainda dentro do prazo
        db.execute(
            text(
                "INSERT INTO pedido_impressao (id, escola_id, autor_id, atribuicao_id, arquivo_id, tipo, titulo,"
                " data_aplicacao, copias, copias_calculadas, copias_adaptadas, frente_verso, colorido, grampear,"
                " status, publicado, criado_em) SELECT gen_random_uuid(), escola_id, autor_id, atribuicao_id,"
                " arquivo_id, tipo, 'Outro', current_date + 5, copias, copias_calculadas, 0, true, false, false,"
                " 'aprovada', false, now() FROM pedido_impressao WHERE id = :i"
            ),
            {"i": pid},
        )
        db.execute(text("UPDATE pedido_impressao SET data_aplicacao = current_date - 400 WHERE id = :i"), {"i": pid})
    with Session(owner_engine) as db, db.begin():
        assert elimina_vencidos(db)["pedidos"] == 1
    assert len(_bins() - antes) == 1  # o arquivo continua, o outro pedido ainda usa


def test_orfaos_do_disco(mundo, owner_engine):
    raiz = Path(get_settings().storage_dir) / "00000000-0000-0000-0000-000000000001"
    raiz.mkdir(parents=True, exist_ok=True)
    velho, novo = raiz / "11111111-1111-1111-1111-111111111111.bin", raiz / "22222222-2222-2222-2222-222222222222.bin"
    velho.write_bytes(b"x")
    novo.write_bytes(b"x")
    os.utime(velho, (0, datetime.now(UTC).timestamp() - 7200))
    with Session(owner_engine) as db, db.begin():
        assert varre_orfaos(db) == 1
    assert not velho.exists() and novo.exists()
    novo.unlink()


def test_worker_inclui_retencao(mundo, owner_engine):
    with Session(owner_engine) as db, db.begin():
        r = processar(db, agora=datetime.now(UTC) + timedelta(days=1))
    assert {"eliminados_pedidos", "eliminados_anexos", "eliminados_orfaos"} <= set(r)
