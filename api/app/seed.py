"""Dados de demonstração (escola fictícia) para desenvolvimento e screenshots.

    python -m app.seed            # apaga e recria a escola de demonstração

Todos os nomes são gerados aleatoriamente e fictícios. Contas de demonstração (só em dev):
senha `caderneta-demo` para todas; a equipe usa 2FA com o segredo DEMO_TOTP abaixo
(adicione-o num app autenticador ou gere o código com `python -m app.seed --codigo`).
"""

import random
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pyotp
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from app.calendario import feriados_sugeridos
from app.config import get_settings
from app.models import (
    Aluno,
    AnoLetivo,
    Anotacao,
    AnotacaoVersao,
    Atribuicao,
    Aula,
    Avaliacao,
    Convite,
    Disciplina,
    Escola,
    Evento,
    FichaSaude,
    Frequencia,
    Matricula,
    Nota,
    Papel,
    PedidoComentario,
    PedidoImpressao,
    Periodo,
    StatusNota,
    StatusPedido,
    StatusPresenca,
    TipoAnotacao,
    TipoEvento,
    TipoPedido,
    TipoPeriodo,
    Turma,
    Usuario,
    UsuarioPerfil,
    VinculoResponsavel,
)
from app.routers.escola import divide_periodos
from app.security import cifra, cifra_json, hash_senha, novo_token

SENHA_DEMO = "caderneta-demo"
DEMO_TOTP = "CADERNETADEMOTOTPSEGREDOXYZABCDE"
NOME_ESCOLA = "Colégio Horizonte (demonstração)"

NOMES_F = [
    "Ana",
    "Beatriz",
    "Camila",
    "Daniela",
    "Eduarda",
    "Fernanda",
    "Gabriela",
    "Helena",
    "Isabela",
    "Júlia",
    "Larissa",
    "Manuela",
    "Natália",
    "Olívia",
    "Paula",
    "Rafaela",
    "Sofia",
    "Valentina",
    "Lívia",
    "Cecília",
]
NOMES_M = [
    "Arthur",
    "Bernardo",
    "Caio",
    "Davi",
    "Enzo",
    "Felipe",
    "Gabriel",
    "Heitor",
    "Igor",
    "João",
    "Lucas",
    "Mateus",
    "Nicolas",
    "Otávio",
    "Pedro",
    "Rafael",
    "Samuel",
    "Thiago",
    "Vicente",
    "Lorenzo",
]
SOBRENOMES = [
    "Almeida",
    "Barbosa",
    "Cardoso",
    "Costa",
    "Dias",
    "Ferreira",
    "Gomes",
    "Lima",
    "Martins",
    "Melo",
    "Moreira",
    "Nunes",
    "Oliveira",
    "Pereira",
    "Ribeiro",
    "Rocha",
    "Santos",
    "Souza",
    "Teixeira",
    "Vieira",
]
DISCIPLINAS = ["Português", "Matemática", "Ciências", "História", "Geografia", "Inglês", "Artes", "Educação Física"]
TURMAS = [
    ("6º A", "6º ano", "manhã"),
    ("6º B", "6º ano", "tarde"),
    ("7º A", "7º ano", "manhã"),
    ("7º B", "7º ano", "tarde"),
    ("8º A", "8º ano", "manhã"),
    ("9º A", "9º ano", "manhã"),
]
ALERTAS = [
    (
        {"alergias": "Amendoim (anafilaxia)", "medicamentos": "Adrenalina autoinjetável na mochila"},
        "Alergia grave a amendoim: adrenalina na mochila",
    ),
    ({"condicoes": "Asma", "medicamentos": "Bombinha de salbutamol"}, "Asma: pode usar a bombinha a qualquer momento"),
    ({"condicoes": "Diabetes tipo 1", "medicamentos": "Insulina"}, "Diabetes tipo 1: pode lanchar em sala"),
    ({"necessidades_especificas": "Baixa visão"}, "Baixa visão: sentar na frente, provas com fonte ampliada"),
]


def _usuario(db: Session, escola: Escola, email: str, nome: str, papel: Papel, staff: bool = False) -> Usuario:
    u = db.scalar(select(Usuario).where(Usuario.email == email))
    if not u:
        u = Usuario(id=uuid.uuid4(), email=email, nome=nome, senha_hash=hash_senha(SENHA_DEMO))
        if staff:
            u.totp_secret_enc = cifra(DEMO_TOTP, str(u.id))
            u.totp_ativo = True
        db.add(u)
        db.flush()
    db.add(UsuarioPerfil(usuario_id=u.id, escola_id=escola.id, papel=papel))
    return u


def seed() -> None:
    s = get_settings()
    if s.env == "prod":
        raise SystemExit("O seed de demonstração não roda em produção.")
    rnd = random.Random(42)
    engine = create_engine(s.owner_database_url)
    with Session(engine) as db, db.begin():
        db.execute(delete(Escola).where(Escola.nome == NOME_ESCOLA))
        db.execute(delete(Usuario).where(Usuario.email.like("%@demo.caderneta.dev")))
        e = Escola(id=uuid.uuid4(), nome=NOME_ESCOLA, cidade="São Paulo", uf="SP")
        db.add(e)
        db.flush()
        ano = AnoLetivo(
            escola_id=e.id, ano=2026, tipo_periodo=TipoPeriodo.bimestre, inicio=date(2026, 2, 2), fim=date(2026, 12, 11)
        )
        db.add(ano)
        db.flush()
        for i, (a, b) in enumerate(divide_periodos(ano.inicio, ano.fim, 4), 1):
            db.add(Periodo(escola_id=e.id, ano_letivo_id=ano.id, numero=i, nome=f"{i}º bimestre", inicio=a, fim=b))
        disc = {n: Disciplina(escola_id=e.id, nome=n) for n in DISCIPLINAS}
        turmas = [Turma(escola_id=e.id, ano_letivo_id=ano.id, nome=n, serie=sr, turno=tu) for n, sr, tu in TURMAS]
        db.add_all([*disc.values(), *turmas])
        db.flush()

        dom = "demo.caderneta.dev"
        _usuario(db, e, f"direcao@{dom}", "Regina Prado", Papel.admin, staff=True)
        _usuario(db, e, f"coordenacao@{dom}", "Marcos Tavares", Papel.coordenacao, staff=True)
        profs = {
            "Matemática": _usuario(db, e, f"ana.matematica@{dom}", "Ana Ribeiro", Papel.professor),
            "Português": _usuario(db, e, f"carlos.portugues@{dom}", "Carlos Menezes", Papel.professor),
            "Ciências": _usuario(db, e, f"luiza.ciencias@{dom}", "Luiza Fontes", Papel.professor),
            "História": _usuario(db, e, f"paulo.historia@{dom}", "Paulo Andrade", Papel.professor),
        }
        for t in turmas:
            for d, p in profs.items():
                db.add(Atribuicao(escola_id=e.id, turma_id=t.id, disciplina_id=disc[d].id, professor_id=p.id))

        resp_demo = _usuario(db, e, f"familia@{dom}", "Patrícia Moreira", Papel.responsavel)
        aluno_demo_user = _usuario(db, e, f"aluno@{dom}", "Lucas Moreira", Papel.aluno)

        n = 0
        for t_i, t in enumerate(turmas):
            idade = 11 + int(t.serie[0]) - 6
            for k in range(rnd.randint(18, 24)):
                n += 1
                fem = rnd.random() < 0.5
                nome = rnd.choice(NOMES_F if fem else NOMES_M)
                sobrenome = f"{rnd.choice(SOBRENOMES)} {rnd.choice(SOBRENOMES)}"
                usuario_id = None
                if sobrenome == "Moreira Lima":  # evita coincidência com a família de demonstração
                    sobrenome = "Moreira Santos"
                if t_i == 2 and k == 0:
                    nome, sobrenome, usuario_id = "Lucas", "Moreira Lima", aluno_demo_user.id
                if t_i == 0 and k == 0:
                    nome, sobrenome = "Sofia", "Moreira Lima"
                nasc = date(2026 - idade - 1, rnd.randint(1, 12), rnd.randint(1, 28))
                a = Aluno(
                    escola_id=e.id,
                    nome=nome,
                    sobrenome=sobrenome,
                    data_nascimento=nasc,
                    ra=f"2026{n:04d}",
                    usuario_id=usuario_id,
                )
                db.add(a)
                db.flush()
                db.add(Matricula(escola_id=e.id, aluno_id=a.id, turma_id=t.id, ano_letivo_id=ano.id))
                if sobrenome == "Moreira Lima":
                    db.add(
                        VinculoResponsavel(
                            escola_id=e.id,
                            aluno_id=a.id,
                            usuario_id=resp_demo.id,
                            nome="Patrícia Moreira",
                            tipo="mae",
                            email=f"familia@{dom}",
                            telefone="(11) 98765-4321",
                            emergencia=True,
                        )
                    )
                    db.add(
                        VinculoResponsavel(
                            escola_id=e.id, aluno_id=a.id, nome="Roberto Lima", tipo="pai", telefone="(11) 91234-5678"
                        )
                    )
                else:
                    mae = f"{rnd.choice(NOMES_F)} {sobrenome.split()[0]}"
                    v = VinculoResponsavel(
                        escola_id=e.id,
                        aluno_id=a.id,
                        nome=mae,
                        tipo="mae",
                        email=f"resp{n}@{dom}",
                        telefone=f"(11) 9{rnd.randint(1000, 9999)}-{rnd.randint(1000, 9999)}",
                        emergencia=True,
                    )
                    db.add(v)
                    db.flush()
                    if rnd.random() < 0.25:  # alguns convites ainda pendentes
                        _, h = novo_token()
                        db.add(
                            Convite(
                                escola_id=e.id,
                                email=v.email,
                                nome=v.nome,
                                papel=Papel.responsavel,
                                vinculo_id=v.id,
                                aluno_id=a.id,
                                token_hash=h,
                                expira_em=date(2030, 1, 1),
                            )
                        )
                if rnd.random() < 0.12 or (nome == "Lucas" and usuario_id):
                    dados, alerta = rnd.choice(ALERTAS) if not usuario_id else ALERTAS[1]
                    db.add(
                        FichaSaude(
                            aluno_id=a.id,
                            escola_id=e.id,
                            dados_enc=cifra_json(dados, str(a.id)),
                            alerta_enc=cifra(alerta, f"alerta:{a.id}"),
                        )
                    )
        db.flush()
        avs, aulas = _seed_m2(db, e, ano, rnd)
        _seed_m4(db, e, turmas)
        _seed_m5(db, e)
        _seed_m6(db, e, ano)
        _seed_anotacoes(db, e, ano)
        print(f"Escola de demonstração criada com {n} alunos, {len(turmas)} turmas, {avs} avaliações e {aulas} aulas.")


def _seed_m4(db: Session, e: Escola, turmas: list[Turma]) -> None:
    """Calendário: feriados nacionais do ano e alguns eventos próximos de hoje."""
    hoje = date.today()
    for f in feriados_sugeridos(hoje.year):
        if f["nacional"]:
            db.add(
                Evento(
                    escola_id=e.id,
                    tipo=TipoEvento.feriado,
                    titulo=f["nome"],
                    descricao=f["base"],
                    inicio=f["data"],
                    fim=f["data"],
                )
            )

    def ev(tipo: TipoEvento, titulo: str, dias: int, duracao: int = 1, turma: Turma | None = None) -> None:
        ini = hoje + timedelta(days=dias)
        db.add(
            Evento(
                escola_id=e.id,
                turma_id=turma.id if turma else None,
                tipo=tipo,
                titulo=titulo,
                inicio=ini,
                fim=ini + timedelta(days=duracao - 1),
            )
        )

    ev(TipoEvento.evento, "Reunião de pais", 3)
    ev(TipoEvento.sem_aula, "Conselho de classe", 9, 2)
    ev(TipoEvento.evento, "Feira de ciências", 14)
    ev(TipoEvento.evento, "Formatura do 9º ano", 25)
    ev(TipoEvento.prazo, "Entrega do trabalho de História", 6, turma=turmas[0])
    ev(TipoEvento.evento, "Passeio ao Museu da Língua Portuguesa", 11, turma=turmas[0])
    ev(TipoEvento.prazo, "Entrega do projeto de Ciências", 8, turma=turmas[1])


def _seed_m6(db: Session, e: Escola, ano: AnoLetivo) -> None:
    """Ano seguinte já criado (planejado), para demonstrar a virada de ano."""
    novo = AnoLetivo(
        escola_id=e.id,
        ano=ano.ano + 1,
        tipo_periodo=TipoPeriodo.bimestre,
        inicio=date(ano.ano + 1, 2, 1),
        fim=date(ano.ano + 1, 12, 10),
        aberto=False,
    )
    db.add(novo)
    db.flush()
    for i, (a, b) in enumerate(divide_periodos(novo.inicio, novo.fim, 4), 1):
        db.add(Periodo(escola_id=e.id, ano_letivo_id=novo.id, numero=i, nome=f"{i}º bimestre", inicio=a, fim=b))


def _seed_anotacoes(db: Session, e: Escola, ano: AnoLetivo) -> None:
    """Anotações do aluno demo (Lucas), uma de cada tipo, uma delas com duas versões."""
    lucas = db.scalar(
        select(Aluno).where(Aluno.escola_id == e.id, Aluno.nome == "Lucas", Aluno.sobrenome == "Moreira Lima")
    )
    dom = "demo.caderneta.dev"
    por_email = {u.email: u for u in db.scalars(select(Usuario).where(Usuario.email.like(f"%@{dom}")))}
    assert lucas is not None

    def nota(email, tipo, corpo, visivel=False, versoes=()):
        a = Anotacao(
            escola_id=e.id,
            aluno_id=lucas.id,
            ano_letivo_id=ano.id,
            autor_id=por_email[f"{email}@{dom}"].id,
            tipo=tipo,
            corpo=corpo,
            visivel_responsaveis=visivel,
        )
        db.add(a)
        db.flush()
        antigos = [*versoes, corpo]
        for i, c in enumerate(antigos, 1):
            db.add(
                AnotacaoVersao(
                    escola_id=e.id,
                    anotacao_id=a.id,
                    versao=i,
                    tipo=tipo,
                    corpo=c,
                    visivel_responsaveis=visivel,
                    editado_por=a.autor_id,
                )
            )
        a.versao = len(antigos)

    nota(
        "ana.matematica",
        TipoAnotacao.pedagogica,
        "Rende muito mais em atividades em dupla. Precisa de apoio com frações.",
        versoes=("Rende mais em atividades em dupla.",),
    )
    nota(
        "carlos.portugues",
        TipoAnotacao.elogio,
        "Ajudou os colegas na leitura em voz alta e organizou o sarau da turma.",
    )
    nota(
        "ana.matematica",
        TipoAnotacao.ocorrencia,
        "Chegou atrasado três vezes na última semana. Conversei com ele.",
        visivel=True,
    )
    nota(
        "coordenacao",
        TipoAnotacao.reservada,
        "Família em reorganização; evitar tratar do assunto em sala. Acompanhar com a orientação.",
    )


def _pdf_demo(titulo: str) -> bytes:
    """PDF mínimo e válido, só para a demonstração."""
    texto = titulo.replace("(", "").replace(")", "")
    conteudo = f"BT /F1 18 Tf 72 720 Td ({texto}) Tj ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(conteudo) + conteudo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)


def _seed_m5(db: Session, e: Escola) -> None:
    """Pedidos de impressão em vários estados, incluindo um trabalho publicado para a turma da família demo."""
    from app.arquivos import grava

    hoje = date.today()
    turma_lucas = db.scalar(
        select(Matricula.turma_id)
        .join(Aluno, Aluno.id == Matricula.aluno_id)
        .where(Aluno.nome == "Lucas", Aluno.sobrenome == "Moreira Lima", Aluno.escola_id == e.id)
    )
    atribs = {
        (a.turma_id, a.disciplina.nome): a for a in db.scalars(select(Atribuicao).where(Atribuicao.escola_id == e.id))
    }
    turmas = list(db.scalars(select(Turma).where(Turma.escola_id == e.id).order_by(Turma.nome)))

    def pedido(turma_id, disc, tipo, titulo, dias, status, publicado=False, copias=None):
        a = atribs[(turma_id, disc)]
        arq = grava(db, escola_id=e.id, usuario_id=a.professor_id, nome=f"{titulo}.pdf", dados=_pdf_demo(titulo))
        alunos = db.scalar(select(func.count()).select_from(Matricula).where(Matricula.turma_id == turma_id)) or 0
        p = PedidoImpressao(
            escola_id=e.id,
            autor_id=a.professor_id,
            atribuicao_id=a.id,
            arquivo_id=arq.id,
            tipo=tipo,
            titulo=titulo,
            data_aplicacao=hoje + timedelta(days=dias),
            copias=copias or alunos + 2,
            copias_calculadas=alunos + 2,
            status=status,
            publicado=publicado,
            enviado_em=None if status == StatusPedido.rascunho else datetime.now(UTC),
        )
        db.add(p)
        db.flush()
        return p

    pedido(turmas[0].id, "Matemática", TipoPedido.prova, "Prova de Frações", 5, StatusPedido.enviada)
    pedido(turmas[1].id, "Ciências", TipoPedido.prova, "Prova do Sistema Solar", 9, StatusPedido.aprovada, copias=26)
    pedido(turmas[2].id, "Português", TipoPedido.prova, "Prova de Interpretação de Texto", 6, StatusPedido.aprovada)
    pedido(
        turma_lucas, "História", TipoPedido.trabalho, "Trabalho sobre o Brasil Colônia", 12, StatusPedido.aprovada, True
    )
    pedido(turmas[0].id, "Matemática", TipoPedido.lista, "Lista de exercícios de Equações", 3, StatusPedido.rascunho)
    pedido(turmas[3].id, "Ciências", TipoPedido.prova, "Prova de Ecossistemas", 1, StatusPedido.impressa)
    ajustes = pedido(turmas[4].id, "Português", TipoPedido.prova, "Prova de Gramática", 8, StatusPedido.ajustes)
    db.add(
        PedidoComentario(
            escola_id=e.id,
            pedido_id=ajustes.id,
            autor_id=None,
            corpo="A questão 4 está sem alternativa correta. Pode revisar?",
        )
    )


def _seed_m2(db: Session, e: Escola, ano: AnoLetivo, rnd: random.Random) -> tuple[int, int]:
    """Ano letivo em andamento: 1º e 2º bimestres fechados, 3º completo, 4º com a primeira prova lançada."""
    hoje = date.today()
    periodos = list(db.scalars(select(Periodo).where(Periodo.ano_letivo_id == ano.id).order_by(Periodo.numero)))
    for p in periodos[:2]:
        p.fechado = True
    nivel: dict[uuid.UUID, float] = {}
    n_av = n_aulas = 0
    for a in db.scalars(select(Atribuicao).where(Atribuicao.escola_id == e.id)):
        mats = list(db.scalars(select(Matricula).where(Matricula.turma_id == a.turma_id)))
        for m in mats:
            nivel.setdefault(m.aluno_id, rnd.uniform(4.5, 9.6))
        for p in periodos:
            planos = [("Prova 1", "prova", 2, 10), ("Trabalho", "trabalho", 1, 10), ("Prova 2", "prova", 2, 10)]
            if p.numero == 4:
                planos = planos[:1]  # bimestre em andamento
            for i, (nome, tipo, peso, maxima) in enumerate(planos):
                d = p.inicio + timedelta(days=20 + 18 * i)
                if d > hoje:
                    continue
                av = Avaliacao(
                    escola_id=e.id,
                    atribuicao_id=a.id,
                    periodo_id=p.id,
                    nome=nome,
                    tipo=tipo,
                    data=d,
                    peso=Decimal(peso),
                    nota_maxima=Decimal(maxima),
                    publicada=p.numero < 4,
                )
                db.add(av)
                db.flush()
                n_av += 1
                for m in mats:
                    if rnd.random() < 0.03:
                        db.add(
                            Nota(
                                escola_id=e.id,
                                avaliacao_id=av.id,
                                matricula_id=m.id,
                                valor=None,
                                status=StatusNota.falta_justificada,
                            )
                        )
                        continue
                    v = max(0.0, min(10.0, rnd.gauss(nivel[m.aluno_id], 1.3)))
                    db.add(
                        Nota(
                            escola_id=e.id, avaliacao_id=av.id, matricula_id=m.id, valor=Decimal(str(round(v * 2) / 2))
                        )
                    )
            if p.numero == 2:  # recuperação para quem ficou abaixo da média
                rec = Avaliacao(
                    escola_id=e.id,
                    atribuicao_id=a.id,
                    periodo_id=p.id,
                    nome="Recuperação",
                    tipo="recuperacao",
                    recuperacao=True,
                    data=p.fim - timedelta(days=3),
                    peso=Decimal(1),
                    nota_maxima=Decimal(10),
                    publicada=True,
                )
                db.add(rec)
                db.flush()
                n_av += 1
                for m in mats:
                    if nivel[m.aluno_id] < 6.2:
                        v = max(0.0, min(10.0, rnd.gauss(6.5, 1.0)))
                        db.add(
                            Nota(
                                escola_id=e.id,
                                avaliacao_id=rec.id,
                                matricula_id=m.id,
                                valor=Decimal(str(round(v * 2) / 2)),
                            )
                        )
            # Chamada: duas aulas por semana (uma delas dupla), até hoje
            d = p.inicio
            while d <= min(p.fim, hoje):
                if d.weekday() in (1, 3):
                    q = 2 if d.weekday() == 1 else 1
                    aula = Aula(escola_id=e.id, atribuicao_id=a.id, data=d, quantidade=q)
                    db.add(aula)
                    db.flush()
                    n_aulas += 1
                    for m in mats:
                        r = rnd.random()
                        faltoso = nivel[m.aluno_id] < 5.2
                        if r < (0.12 if faltoso else 0.035):
                            st = StatusPresenca.justificada if rnd.random() < 0.3 else StatusPresenca.falta
                            db.add(
                                Frequencia(
                                    escola_id=e.id,
                                    aula_id=aula.id,
                                    matricula_id=m.id,
                                    status=st,
                                    justificativa="Atestado médico" if st == StatusPresenca.justificada else None,
                                )
                            )
                        elif r < 0.05:
                            db.add(
                                Frequencia(
                                    escola_id=e.id, aula_id=aula.id, matricula_id=m.id, status=StatusPresenca.atraso
                                )
                            )
                d += timedelta(days=1)
    return n_av, n_aulas


if __name__ == "__main__":
    if "--codigo" in sys.argv:
        print(pyotp.TOTP(DEMO_TOTP).now())
    else:
        seed()
