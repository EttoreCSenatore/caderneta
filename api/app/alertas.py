"""Alertas automáticos: faltas (15% e 20%) e nota nova publicada.

O texto dentro do app pode citar o aluno; o e-mail nunca leva conteúdo (ver `notificacoes`).
"""

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AlertaFalta,
    Aluno,
    Atribuicao,
    Aula,
    Avaliacao,
    Frequencia,
    Matricula,
    Nota,
    StatusPresenca,
)
from app.notificacoes import equipe_da_escola, familia_dos_alunos, notificar

NIVEIS_FALTA = (15, 20)


def pct_faltas(db: Session, matricula: Matricula) -> Decimal | None:
    """Faltas (injustificadas e justificadas) sobre as aulas dadas no ano, somando todas as disciplinas da turma."""
    atribs = select(Atribuicao.id).where(Atribuicao.turma_id == matricula.turma_id)
    dadas = db.scalar(select(func.sum(Aula.quantidade)).where(Aula.atribuicao_id.in_(atribs)))
    if not dadas:
        return None
    faltas = db.scalar(
        select(func.sum(Aula.quantidade))
        .join(Frequencia, Frequencia.aula_id == Aula.id)
        .where(
            Frequencia.matricula_id == matricula.id,
            Aula.atribuicao_id.in_(atribs),
            Frequencia.status.in_([StatusPresenca.falta, StatusPresenca.justificada]),
        )
    )
    return Decimal(faltas or 0) * 100 / Decimal(dadas)


def verifica_faltas(db: Session, escola_id: uuid.UUID, matricula_ids: list[uuid.UUID]) -> int:
    """Dispara os alertas de 15% e 20% uma única vez por matrícula e nível. Devolve quantos foram criados."""
    criados = 0
    for mid in set(matricula_ids):
        m = db.get(Matricula, mid)
        if not m:
            continue
        pct = pct_faltas(db, m)
        if pct is None:
            continue
        ja = set(db.scalars(select(AlertaFalta.nivel).where(AlertaFalta.matricula_id == mid)))
        novos = [n for n in NIVEIS_FALTA if pct >= n and n not in ja]
        if not novos:
            continue
        nivel = max(novos)
        for n in novos:  # se pulou direto para 20%, registra o 15% também, sem avisar duas vezes
            db.add(AlertaFalta(escola_id=escola_id, matricula_id=mid, nivel=n))
        aluno = db.get(Aluno, m.aluno_id)
        nome = f"{aluno.nome} {aluno.sobrenome}" if aluno else "O aluno"
        texto = f"{nome} chegou a {nivel}% de faltas no ano."
        notificar(
            db,
            escola_id=escola_id,
            usuarios=set(familia_dos_alunos(db, escola_id, [m.aluno_id])) | equipe_da_escola(db, escola_id),
            tipo="falta",
            titulo=f"Alerta de faltas: {nivel}%",
            corpo=texto,
            url="/",
        )
        criados += 1
    return criados


def notifica_nota_publicada(db: Session, escola_id: uuid.UUID, avaliacao: Avaliacao, disciplina: str) -> int:
    """Avisa a família e o aluno quando uma avaliação é publicada. Só quem tem nota lançada; sem valores no texto."""
    alunos = list(
        db.scalars(
            select(Matricula.aluno_id)
            .join(Nota, Nota.matricula_id == Matricula.id)
            .where(Nota.avaliacao_id == avaliacao.id, Nota.valor.is_not(None))
        )
    )
    if not alunos:
        return 0
    return notificar(
        db,
        escola_id=escola_id,
        usuarios=familia_dos_alunos(db, escola_id, alunos, incluir_alunos=True),
        tipo="nota",
        titulo="Nova nota publicada",
        corpo=f"{disciplina}: {avaliacao.nome}",
        url="/",
    )
