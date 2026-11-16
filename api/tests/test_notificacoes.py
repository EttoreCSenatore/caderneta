"""M3: notificações (no app e e-mail mínimo), horário silencioso, lembrete, alertas e retenção."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import mail
from app.notificacoes import limpa_antigas, processar, proximo_envio

SP = "America/Sao_Paulo"


def _aviso(c, **kw):
    r = c.post("/api/avisos", json={"titulo": "Reunião secreta de pais", "corpo": "Sexta, 19h.", **kw})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _caixa(c, **p):
    return c.get("/api/notificacoes", params=p).json()


def _depois(horas=48):
    return datetime.now(UTC) + timedelta(hours=horas)


def test_aviso_notifica_familia_e_aluno_mas_nao_o_autor(mundo, entrar):
    a, _ = mundo
    prof = entrar("prof.a@teste.com")
    _aviso(prof, turma_id=str(a.turma.id))
    mae, aluno = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com")
    assert [n["tipo"] for n in _caixa(mae)] == ["aviso"]
    assert len(_caixa(aluno)) == 1
    assert _caixa(prof) == []
    assert _caixa(entrar("mae.b@teste.com")) == []  # outra escola
    assert mae.get("/api/notificacoes/contagem").json() == {"nao_lidas": 1}


def test_marcar_lida_so_as_proprias(mundo, entrar):
    a, _ = mundo
    _aviso(entrar("coord.a@teste.com"))
    mae, aluno = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com")
    nid = _caixa(mae)[0]["id"]
    assert aluno.post(f"/api/notificacoes/{nid}/lida").status_code == 404
    assert mae.post(f"/api/notificacoes/{nid}/lida").json()["lida"] is True
    assert mae.get("/api/notificacoes/contagem").json() == {"nao_lidas": 0}
    assert aluno.post("/api/notificacoes/lidas").json() == {"marcadas": 1}


def test_email_generico_agrupado_e_so_para_adultos(mundo, entrar, owner_engine):
    a, _ = mundo
    coord = entrar("coord.a@teste.com")
    _aviso(coord, titulo="Prova de matemática do João")
    _aviso(coord, titulo="Passeio")
    with Session(owner_engine) as db, db.begin():
        r = processar(db, agora=_depois())
    assert r["emails"] == 1  # só a mãe; a conta do aluno (menor) não recebe e-mail
    (msg,) = mail.outbox
    assert msg["To"] == "mae.a@teste.com"
    corpo = msg.get_content() + msg["Subject"]
    assert "2 novidades" in corpo and "/notificacoes" in corpo
    assert "João" not in corpo and "Passeio" not in corpo and "matemática" not in corpo
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=_depois(72))["emails"] == 0  # não reenvia


def test_preferencia_desliga_email(mundo, entrar, owner_engine):
    a, _ = mundo
    mae = entrar("mae.a@teste.com")
    assert mae.get("/api/notificacoes-preferencias").json() == {
        "email": True,
        "silencio_inicio": "21:00",
        "silencio_fim": "07:00",
    }
    r = mae.put(
        "/api/notificacoes-preferencias", json={"email": False, "silencio_inicio": "22:00", "silencio_fim": "06:30"}
    )
    assert r.json()["silencio_fim"] == "06:30"
    _aviso(entrar("coord.a@teste.com"))
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=_depois())["emails"] == 0
    assert len(_caixa(mae)) == 1  # continua no app


def test_horario_silencioso():
    ini, fim = time(21, 0), time(7, 0)
    noite = datetime(2026, 11, 16, 23, 30, tzinfo=UTC) - timedelta(hours=-3)  # 02:30 UTC = 23:30 em SP
    assert proximo_envio(noite, SP, ini, fim) == datetime(2026, 11, 17, 10, 0, tzinfo=UTC)  # 07:00 SP
    madrugada = datetime(2026, 11, 17, 6, 0, tzinfo=UTC)  # 03:00 em SP
    assert proximo_envio(madrugada, SP, ini, fim) == datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    tarde = datetime(2026, 11, 16, 17, 0, tzinfo=UTC)  # 14:00 em SP
    assert proximo_envio(tarde, SP, ini, fim) == tarde
    assert proximo_envio(noite, SP, ini, ini) == noite  # início = fim: sem silêncio


def test_email_respeita_enviar_apos(mundo, entrar, owner_engine):
    _aviso(entrar("coord.a@teste.com"))
    with Session(owner_engine) as db, db.begin():
        db.execute(text("UPDATE notificacao SET enviar_apos = now() + interval '5 hours' WHERE email_pendente"))
        assert processar(db, agora=datetime.now(UTC))["emails"] == 0
        assert processar(db, agora=_depois(6))["emails"] == 1


def test_aviso_agendado_notifica_na_hora(mundo, entrar, owner_engine):
    a, _ = mundo
    futuro = _depois(24)
    _aviso(entrar("coord.a@teste.com"), publicar_em=futuro.isoformat())
    mae = entrar("mae.a@teste.com")
    assert _caixa(mae) == []
    with Session(owner_engine) as db, db.begin():
        assert processar(db, agora=futuro - timedelta(minutes=1))["avisos"] == 0
        assert processar(db, agora=futuro + timedelta(minutes=1))["avisos"] == 2  # mãe + conta do aluno
        assert processar(db, agora=futuro + timedelta(minutes=2))["avisos"] == 0  # só uma vez
    assert len(_caixa(mae)) == 1


def test_lembrete_so_aos_pendentes_e_uma_vez_por_dia(mundo, entrar):
    a, _ = mundo
    prof = entrar("prof.a@teste.com")
    aid = _aviso(prof, turma_id=str(a.turma.id), exige_ciente=True)
    mae, aluno = entrar("mae.a@teste.com"), entrar("aluno.a@teste.com")
    mae.post(f"/api/avisos/{aid}/lido", params={"ciente": True})
    assert mae.post(f"/api/avisos/{aid}/lembrete").status_code == 404  # leitor não lembra
    r = prof.post(f"/api/avisos/{aid}/lembrete")
    assert r.json() == {"notificados": 1}  # só o aluno falta
    assert [n["tipo"] for n in _caixa(aluno)] == ["lembrete", "aviso"]
    assert len(_caixa(mae)) == 1
    assert prof.post(f"/api/avisos/{aid}/lembrete").status_code == 429
    assert entrar("prof2.a@teste.com").post(f"/api/avisos/{aid}/lembrete").status_code == 404


def test_mensagem_e_autorizacao_notificam(mundo, entrar):
    a, _ = mundo
    prof, mae = entrar("prof.a@teste.com"), entrar("mae.a@teste.com")
    r = prof.post("/api/conversas", json={"aluno_id": str(a.alunos["joao"].id), "assunto": "Oi", "corpo": "Olá"})
    cid = r.json()["id"]
    assert [n["tipo"] for n in _caixa(mae)] == ["mensagem"]
    mae.post(f"/api/conversas/{cid}/mensagens", json={"corpo": "Oi!"})
    assert [n["tipo"] for n in _caixa(prof)] == ["mensagem"]
    assert _caixa(prof)[0]["corpo"] == "De Mae.A"
    prof.post("/api/autorizacoes", json={"titulo": "Passeio", "descricao": "x", "turma_id": str(a.turma.id)})
    assert [n["tipo"] for n in _caixa(mae)][0] == "autorizacao"


@pytest.fixture
def diario(mundo, entrar, owner_engine):
    a, _ = mundo
    with owner_engine.begin() as db:
        atrib = db.execute(text("SELECT id FROM atribuicao WHERE turma_id = :t"), {"t": a.turma.id}).scalar()
    prof = entrar("prof.a@teste.com")
    d = prof.get(f"/api/atribuicoes/{atrib}/diario").json()
    return {
        "a": a,
        "atrib": str(atrib),
        "prof": prof,
        "periodo": d["periodos"][0]["id"],
        "mat": {x["nome"].split()[0]: x["matricula_id"] for x in d["alunos"]},
    }


def test_nota_publicada_notifica_so_quem_tem_nota_sem_valor(diario, entrar):
    prof, m = diario["prof"], diario["mat"]
    av = prof.post(
        f"/api/atribuicoes/{diario['atrib']}/avaliacoes",
        json={"periodo_id": diario["periodo"], "nome": "Prova 1", "peso": 1},
    ).json()["id"]
    prof.put(f"/api/avaliacoes/{av}/notas", json={"notas": [{"matricula_id": m["João"], "valor": 7.5}]})
    mae = entrar("mae.a@teste.com")
    assert _caixa(mae) == []
    prof.post(f"/api/avaliacoes/{av}/publicar", json={"publicada": True})
    (n,) = _caixa(mae)
    assert n["tipo"] == "nota" and "7" not in n["corpo"] and "Matemática" in n["corpo"]
    prof.post(f"/api/avaliacoes/{av}/publicar", json={"publicada": False})
    prof.post(f"/api/avaliacoes/{av}/publicar", json={"publicada": True})
    assert len(_caixa(mae)) == 1  # republicar não notifica de novo
    assert len(_caixa(entrar("aluno.a@teste.com"))) == 1


def _aula(c, ctx, dia: int, faltou: bool):
    regs = [{"matricula_id": ctx["mat"]["João"], "status": "falta" if faltou else "presente"}]
    r = c.post(
        f"/api/atribuicoes/{ctx['atrib']}/aulas",
        json={"data": str(date(2026, 3, dia)), "quantidade": 1, "registros": regs},
    )
    assert r.status_code == 201, r.text


def test_alerta_de_faltas_15_e_20_uma_vez(diario, entrar):
    prof, mae, coord = diario["prof"], entrar("mae.a@teste.com"), entrar("coord.a@teste.com")
    for d in range(2, 8):  # 6 presenças
        _aula(prof, diario, d, False)
    _aula(prof, diario, 9, True)  # 1/7 = 14,3%: ainda sem alerta
    assert _caixa(mae) == []
    _aula(prof, diario, 10, True)  # 2/8 = 25%: passa de 15% e de 20% de uma vez
    (n,) = _caixa(mae)
    assert n["tipo"] == "falta" and "20%" in n["corpo"] and "João" in n["corpo"]
    assert any(x["tipo"] == "falta" for x in _caixa(coord))  # a coordenação também é avisada
    _aula(prof, diario, 11, True)
    assert len(_caixa(mae)) == 1  # sem repetir


def test_retencao(mundo, entrar, owner_engine):
    _aviso(entrar("coord.a@teste.com"))
    with Session(owner_engine) as db, db.begin():
        db.execute(text("UPDATE notificacao SET lida_em = now(), criado_em = now() - interval '91 days'"))
        assert limpa_antigas(db) == 2
    _aviso(entrar("coord.a@teste.com"))
    with Session(owner_engine) as db, db.begin():
        db.execute(text("UPDATE notificacao SET criado_em = now() - interval '91 days'"))
        assert limpa_antigas(db) == 0  # não lida e com menos de 180 dias fica
        db.execute(text("UPDATE notificacao SET criado_em = now() - interval '181 days'"))
        assert limpa_antigas(db) == 2
