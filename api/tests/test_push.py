"""Push sem conteúdo: inscrição só de adultos, VAPID, envio pelo worker, limpeza e retenção."""

import base64
import json
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import push
from app.config import get_settings
from app.notificacoes import limpa_inscricoes, processar


class ServicoDePush:
    """Serviço de push falso: guarda o que recebe e responde com o status configurado."""

    def __init__(self):
        self.recebidos: list[dict] = []
        self.status = 201
        dono = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                dono.recebidos.append(
                    {
                        "path": self.path,
                        "h": {k.lower(): v for k, v in self.headers.items()},
                        "corpo": self.rfile.read(n),
                    }
                )
                self.send_response(dono.status)
                self.end_headers()

            def log_message(self, *a):
                pass

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.porta = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def url(self, nome="aparelho1"):
        return f"http://127.0.0.1:{self.porta}/push/{nome}"

    def fecha(self):
        self.srv.shutdown()


@pytest.fixture
def servico(monkeypatch):
    s = get_settings()
    privada, publica = push.gerar_chaves()
    monkeypatch.setattr(s, "vapid_private_key", privada)
    monkeypatch.setattr(s, "vapid_public_key", publica)
    monkeypatch.setattr(s, "vapid_subject", "mailto:teste@escola.com")
    monkeypatch.setattr(s, "push_hosts_extra", "127.0.0.1")
    srv = ServicoDePush()
    yield srv
    srv.fecha()


def _depois(h=48):
    return datetime.now(UTC) + timedelta(hours=h)


def test_endpoints_permitidos():
    ok = [
        "https://fcm.googleapis.com/fcm/send/abc",
        "https://updates.push.services.mozilla.com/wpush/v2/abc",
        "https://web.push.apple.com/abc",
        "https://wns2-par02p.notify.windows.com/?token=x",
    ]
    ruins = [
        "http://fcm.googleapis.com/x",  # sem TLS
        "https://evil.com/fcm.googleapis.com",
        "https://fcm.googleapis.com.evil.com/x",
        "https://127.0.0.1/x",
        "https://localhost/x",
        "https://user:pass@fcm.googleapis.com/x",
        "https://fcm.googleapis.com:8443/x",
        "ftp://fcm.googleapis.com/x",
        "https://169.254.169.254/latest",
        "https://" + "a" * 1000 + ".googleapis.com/",
    ]
    assert all(push.endpoint_valido(u) for u in ok)
    assert not any(push.endpoint_valido(u) for u in ruins)


def test_envio_vazio_com_vapid_valido(servico):
    assert push.envia(servico.url()) == 201
    (r,) = servico.recebidos
    assert r["corpo"] == b"" and r["h"]["ttl"] == "3600" and r["h"]["content-length"] == "0"
    auth = r["h"]["authorization"]
    jwt = auth.split("t=")[1].split(",")[0]
    k = auth.split("k=")[1]
    assert k == get_settings().vapid_public_key
    cab, corpo, sig = jwt.split(".")
    pad = lambda x: x + "=" * (-len(x) % 4)  # noqa: E731
    claims = json.loads(base64.urlsafe_b64decode(pad(corpo)))
    assert claims["aud"] == f"http://127.0.0.1:{servico.porta}" and claims["sub"] == "mailto:teste@escola.com"
    assert claims["exp"] > datetime.now(UTC).timestamp()
    bruta = base64.urlsafe_b64decode(pad(sig))
    chave = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), base64.urlsafe_b64decode(pad(k)))
    chave.verify(
        encode_dss_signature(int.from_bytes(bruta[:32], "big"), int.from_bytes(bruta[32:], "big")),
        f"{cab}.{corpo}".encode(),
        ec.ECDSA(hashes.SHA256()),
    )  # levanta se a assinatura estiver errada
    assert serialization.Encoding.X962  # chave pública no formato X9.62 não comprimido
    assert len(base64.urlsafe_b64decode(pad(k))) == 65


def test_sem_chaves_o_push_fica_desligado(mundo, entrar):
    mae = entrar("mae.a@teste.com")
    assert mae.get("/api/push/config").json() == {"ativo": False, "chave_publica": None, "permitido": True}
    assert mae.post("/api/push/inscricoes", json={"endpoint": "https://fcm.googleapis.com/x/abcdef"}).status_code == 409


def test_inscricao_so_de_adultos_e_enderecos_validos(mundo, entrar, servico):
    mae, aluno = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com")
    cfg = mae.get("/api/push/config").json()
    assert cfg["ativo"] is True and cfg["chave_publica"] == get_settings().vapid_public_key
    assert aluno.get("/api/push/config").json()["permitido"] is False
    assert aluno.post("/api/push/inscricoes", json={"endpoint": servico.url()}).status_code == 403
    assert mae.post("/api/push/inscricoes", json={"endpoint": "https://evil.com/push/abcdef"}).status_code == 422
    assert mae.post("/api/push/inscricoes", json={"endpoint": servico.url()}).status_code == 201
    assert mae.post("/api/push/inscricoes", json={"endpoint": servico.url()}).status_code == 201  # idempotente
    assert mae.get("/api/push/aparelhos").json() == {"aparelhos": 1}
    # outra pessoa entra no mesmo navegador: o aparelho passa a ser dela e some da primeira
    prof = entrar("prof.a@teste.com")
    assert prof.post("/api/push/inscricoes", json={"endpoint": servico.url()}).status_code == 201
    assert mae.get("/api/push/aparelhos").json() == {"aparelhos": 0}
    assert prof.get("/api/push/aparelhos").json() == {"aparelhos": 1}
    assert (
        mae.post("/api/push/cancelar", json={"endpoint": servico.url()}).status_code == 204
    )  # não é dela: nada acontece
    assert prof.get("/api/push/aparelhos").json() == {"aparelhos": 1}
    assert prof.post("/api/push/cancelar", json={"endpoint": servico.url()}).status_code == 204
    assert prof.get("/api/push/aparelhos").json() == {"aparelhos": 0}


def _aviso(c, titulo="Segredo da reunião"):
    assert c.post("/api/avisos", json={"titulo": titulo, "corpo": "texto"}).status_code == 201


def test_worker_envia_um_push_vazio_por_aparelho(mundo, entrar, servico, owner_engine):
    mae, aluno, coord = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com"), entrar("coord.a@teste.com")
    mae.post("/api/push/inscricoes", json={"endpoint": servico.url("celular")})
    mae.post("/api/push/inscricoes", json={"endpoint": servico.url("tablet")})
    _aviso(coord)
    _aviso(coord, "Outro aviso")
    with Session(owner_engine) as db, db.begin():
        r = processar(db, agora=_depois())
    assert r["pushes"] == 2  # dois aparelhos, mesmo com duas notificações: um push por aparelho
    assert sorted(x["path"] for x in servico.recebidos) == ["/push/celular", "/push/tablet"]
    assert all(x["corpo"] == b"" for x in servico.recebidos)
    assert not any(b"Segredo" in json.dumps(x["h"]).encode() for x in servico.recebidos)
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=_depois(72))["pushes"] == 0  # não repete
        pend = db.execute(text("SELECT count(*) FROM notificacao WHERE push_pendente")).scalar()
    assert pend == 0
    assert aluno.get("/api/notificacoes").json()  # a conta do aluno recebe no app, nunca push


def test_nao_envia_se_ja_leu_ou_no_silencio_ou_sem_aparelho(mundo, entrar, servico, owner_engine):
    mae, coord = entrar("mae.a@teste.com"), entrar("coord.a@teste.com")
    mae.post("/api/push/inscricoes", json={"endpoint": servico.url()})
    _aviso(coord)
    with Session(owner_engine) as db, db.begin():
        db.execute(text("UPDATE notificacao SET enviar_apos = now() + interval '5 hours'"))
        assert processar(db, agora=datetime.now(UTC))["pushes"] == 0  # horário silencioso
    mae.post("/api/notificacoes/lidas")
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=_depois(6))["pushes"] == 0  # já leu, não precisa avisar
    assert servico.recebidos == []
    # quem não tem aparelho: a pendência apenas se encerra
    _aviso(coord, "Novo")
    with Session(owner_engine) as db, db.begin():
        mae_id = db.execute(text("SELECT id FROM usuario WHERE email = 'mae.a@teste.com'")).scalar()
        db.execute(text("DELETE FROM push_inscricao WHERE usuario_id = :u"), {"u": mae_id})
        assert processar(db, agora=_depois(60))["pushes"] == 0
        assert db.execute(text("SELECT count(*) FROM notificacao WHERE push_pendente")).scalar() == 0


def test_aparelho_inexistente_e_falha_temporaria(mundo, entrar, servico, owner_engine):
    mae, coord = entrar("mae.a@teste.com"), entrar("coord.a@teste.com")
    mae.post("/api/push/inscricoes", json={"endpoint": servico.url()})
    _aviso(coord)
    servico.status = 503  # falha temporária: mantém a pendência
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=_depois())["pushes"] == 0
        assert db.execute(text("SELECT count(*) FROM notificacao WHERE push_pendente")).scalar() > 0
    servico.status = 201
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=_depois(3))["pushes"] == 1  # na rodada seguinte entrega
    _aviso(coord, "Mais um")
    servico.status = 410  # o aparelho não existe mais: a inscrição é apagada
    with Session(owner_engine) as db, db.begin():
        r = processar(db, agora=_depois(60))
    assert r["inscricoes_removidas"] == 1 and mae.get("/api/push/aparelhos").json() == {"aparelhos": 0}


def test_retencao_de_inscricoes(mundo, entrar, servico, owner_engine):
    mae, prof = entrar("mae.a@teste.com"), entrar("prof.a@teste.com")
    mae.post("/api/push/inscricoes", json={"endpoint": servico.url("parado")})
    prof.post("/api/push/inscricoes", json={"endpoint": servico.url("do-professor")})
    with Session(owner_engine) as db, db.begin():
        db.execute(
            text("UPDATE push_inscricao SET ultimo_uso_em = now() - interval '91 days' WHERE endpoint LIKE '%parado'")
        )
        assert limpa_inscricoes(db) == 1
        db.execute(text("UPDATE usuario SET ativo = false WHERE email = 'prof.a@teste.com'"))  # conta desativada
        assert limpa_inscricoes(db) == 1
    assert mae.get("/api/push/aparelhos").json() == {"aparelhos": 0}


def test_isolamento_do_rls_nas_inscricoes(mundo, entrar, servico, owner_engine):
    entrar("mae.a@teste.com").post("/api/push/inscricoes", json={"endpoint": servico.url()})
    outro = entrar("mae.b@teste.com")
    assert outro.get("/api/push/aparelhos").json() == {"aparelhos": 0}
    assert outro.post("/api/push/cancelar", json={"endpoint": servico.url()}).status_code == 204
    with owner_engine.begin() as db:
        assert db.execute(text("SELECT count(*) FROM push_inscricao")).scalar() == 1  # continua lá
