"""Dados de demonstração (escola fictícia) para desenvolvimento e screenshots.

    python -m app.seed            # apaga e recria a escola de demonstração

Todos os nomes são gerados aleatoriamente e fictícios. Contas de demonstração (só em dev):
senha `caderneta-demo` para todas; a equipe usa 2FA com o segredo DEMO_TOTP abaixo
(adicione-o num app autenticador ou gere o código com `python -m app.seed --codigo`).
"""

import random
import sys
import uuid
from datetime import date

import pyotp
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    Aluno,
    AnoLetivo,
    Atribuicao,
    Convite,
    Disciplina,
    Escola,
    FichaSaude,
    Matricula,
    Papel,
    Periodo,
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
        print(f"Escola de demonstração criada com {n} alunos e {len(turmas)} turmas.")


if __name__ == "__main__":
    if "--codigo" in sys.argv:
        print(pyotp.TOTP(DEMO_TOTP).now())
    else:
        seed()
