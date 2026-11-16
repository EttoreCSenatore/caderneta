"""Virada de ano: turmas do novo ano, rematrícula em lote, encerramento do ano e linha do tempo do aluno."""

import re
import uuid
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.audit import registrar
from app.deps import Contexto, aluno_visivel, com_perfil, equipe, so_admin
from app.models import (
    STAFF,
    Aluno,
    AnoLetivo,
    Atribuicao,
    Matricula,
    Papel,
    SituacaoAluno,
    Turma,
)
from app.routers.boletim import monta_boletim
from app.routers.turmas import turma_visivel

router = APIRouter(tags=["historico"])
ULTIMA_SERIE = 9  # depois do 9º ano o aluno conclui o ensino fundamental


class Resultado(StrEnum):
    aprovado = "aprovado"
    retido = "retido"
    transferido = "transferido"
    concluiu = "concluiu"


class ItemIn(BaseModel):
    aluno_id: uuid.UUID
    resultado: Resultado
    turma_destino_id: uuid.UUID | None = None


class RematriculaIn(BaseModel):
    turma_origem_id: uuid.UUID
    ano_destino_id: uuid.UUID
    itens: list[ItemIn] = Field(min_length=1, max_length=200)


class TurmasDoAnoIn(BaseModel):
    de_ano_letivo_id: uuid.UUID
    avancar_serie: bool = True
    copiar_atribuicoes: bool = True


# --- Séries ---------------------------------------------------------------------------------------------------


def _num_resto(texto: str) -> tuple[int, str] | None:
    m = re.match(r"^\s*(\d+)(.*)$", texto)
    return (int(m.group(1)), m.group(2)) if m else None


def avanca(texto: str) -> str | None:
    """'7º A' → '8º A' e '6º ano' → '7º ano'. Devolve None depois do 9º ano ou se não houver número."""
    nr = _num_resto(texto)
    if not nr or nr[0] >= ULTIMA_SERIE:
        return None
    return f"{nr[0] + 1}{nr[1]}"


def _destinos_sugeridos(origem: Turma, destinos: list[Turma]) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """(turma para quem passa de ano, turma para quem repete), pela mesma letra/nome da turma."""
    prox = avanca(origem.nome)
    aprovado = next((t.id for t in destinos if prox and t.nome == prox), None)
    retido = next((t.id for t in destinos if t.nome == origem.nome), None)
    return aprovado, retido


# --- Ano letivo -----------------------------------------------------------------------------------------------


def _ano(ctx: Contexto, ano_id: uuid.UUID) -> AnoLetivo:
    a = ctx.db.get(AnoLetivo, ano_id)
    if not a:
        raise HTTPException(404, "Ano letivo não encontrado.")
    return a


@router.post("/anos-letivos/{ano_id}/turmas-do-ano", status_code=201)
def turmas_do_ano(ano_id: uuid.UUID, body: TurmasDoAnoIn, ctx: Contexto = Depends(so_admin)):
    """Cria as turmas do novo ano a partir das de um ano anterior (séries avançadas) e copia os professores."""
    destino, origem = _ano(ctx, ano_id), _ano(ctx, body.de_ano_letivo_id)
    if destino.id == origem.id:
        raise HTTPException(422, "Escolha um ano anterior como origem.")
    existentes = {t.nome for t in ctx.db.scalars(select(Turma).where(Turma.ano_letivo_id == destino.id))}
    criadas, puladas = [], []
    for t in ctx.db.scalars(select(Turma).where(Turma.ano_letivo_id == origem.id).order_by(Turma.nome)):
        nome, serie = (avanca(t.nome), avanca(t.serie)) if body.avancar_serie else (t.nome, t.serie)
        if not nome or not serie:
            puladas.append(t.nome)  # 9º ano: os alunos concluem, não há turma seguinte
            continue
        if nome in existentes:
            continue
        nova = Turma(escola_id=ctx.escola_id, ano_letivo_id=destino.id, nome=nome, serie=serie, turno=t.turno)
        ctx.db.add(nova)
        ctx.db.flush()
        existentes.add(nome)
        criadas.append(nome)
        if body.copiar_atribuicoes:
            for a in ctx.db.scalars(select(Atribuicao).where(Atribuicao.turma_id == t.id)):
                ctx.db.add(
                    Atribuicao(
                        escola_id=ctx.escola_id,
                        turma_id=nova.id,
                        disciplina_id=a.disciplina_id,
                        professor_id=a.professor_id,
                    )
                )
    registrar(
        ctx.db,
        "ano.turmas_criadas",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="ano_letivo",
        entidade_id=destino.id,
        detalhes={"criadas": len(criadas)},
    )
    return {"criadas": criadas, "sem_turma_seguinte": puladas}


class EncerrarIn(BaseModel):
    abrir_ano_id: uuid.UUID | None = None  # o ano que passa a ser o atual, na mesma operação


@router.post("/anos-letivos/{ano_id}/encerrar")
def encerrar(ano_id: uuid.UUID, body: EncerrarIn | None = None, ctx: Contexto = Depends(so_admin)):
    """Encerra o ano (todos os períodos fechados) e, se pedido, abre o seguinte.

    Os professores do ano encerrado deixam de ver os alunos que não são mais deles.
    """
    ano = _ano(ctx, ano_id)
    if not ano.aberto:
        raise HTTPException(409, "O ano letivo já está encerrado.")
    abertos = [p.nome for p in ano.periodos if not p.fechado]
    if abertos:
        raise HTTPException(409, "Feche antes os períodos: " + ", ".join(abertos) + ".")
    proximo = None
    if body and body.abrir_ano_id:
        proximo = _ano(ctx, body.abrir_ano_id)
        if proximo.ano <= ano.ano or proximo.aberto:
            raise HTTPException(422, "Escolha um ano posterior, ainda não aberto, para ser o atual.")
    ano.aberto = False
    if proximo:
        proximo.aberto = True
    registrar(
        ctx.db,
        "ano.encerrar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="ano_letivo",
        entidade_id=ano.id,
    )
    return {"ano": ano.ano, "aberto": False, "ano_atual": proximo.ano if proximo else None}


# --- Rematrícula em lote --------------------------------------------------------------------------------------


def _sugestao(ctx: Contexto, aluno: Aluno, ano: AnoLetivo) -> tuple[str, str | None]:
    """('aprovado' | 'retido' | 'pendente', motivo) a partir das situações por disciplina do boletim."""
    sits = {d["situacao"] for d in monta_boletim(ctx, aluno, ano)["disciplinas"]}
    if not sits:
        return "pendente", "Sem disciplinas ou notas no ano."
    if sits & {"reprovado", "reprovado_por_falta"}:
        return "retido", "Reprovado em alguma disciplina" if "reprovado" in sits else "Reprovado por falta"
    if sits == {"aprovado"}:
        return "aprovado", None
    return "pendente", "O ano ainda não foi fechado ou há média abaixo sem decisão."


@router.get("/rematricula/previa")
def previa(turma_id: uuid.UUID, ano_destino_id: uuid.UUID, ctx: Contexto = Depends(equipe)):
    """Alunos da turma com a sugestão calculada pelo boletim e a turma de destino provável."""
    origem = turma_visivel(ctx, turma_id)
    ano_origem, ano_destino = _ano(ctx, origem.ano_letivo_id), _ano(ctx, ano_destino_id)
    if ano_destino.ano <= ano_origem.ano:
        raise HTTPException(422, "O ano de destino precisa ser posterior ao da turma.")
    destinos = list(ctx.db.scalars(select(Turma).where(Turma.ano_letivo_id == ano_destino.id).order_by(Turma.nome)))
    t_aprovado, t_retido = _destinos_sugeridos(origem, destinos)
    ja = set(ctx.db.scalars(select(Matricula.aluno_id).where(Matricula.ano_letivo_id == ano_destino.id)))
    linhas = []
    rows = ctx.db.execute(
        select(Matricula, Aluno)
        .join(Aluno, Aluno.id == Matricula.aluno_id)
        .where(Matricula.turma_id == origem.id)
        .order_by(Aluno.nome, Aluno.sobrenome)
    ).all()
    for m, a in rows:
        sug, motivo = _sugestao(ctx, a, ano_origem)
        linhas.append(
            {
                "aluno_id": a.id,
                "nome": f"{a.nome} {a.sobrenome}",
                "situacao_aluno": a.situacao,
                "matricula_situacao": m.situacao,
                "sugestao": sug,
                "motivo": motivo,
                "turma_destino_sugerida": t_retido if sug == "retido" else t_aprovado,
                "ja_rematriculado": a.id in ja,
            }
        )
    return {
        "turma": {"id": origem.id, "nome": origem.nome, "serie": origem.serie, "ano": ano_origem.ano},
        "ano_destino": {"id": ano_destino.id, "ano": ano_destino.ano},
        "ultima_serie": _num_resto(origem.serie) is not None and avanca(origem.serie) is None,
        "turmas_destino": [{"id": t.id, "nome": t.nome, "serie": t.serie} for t in destinos],
        "alunos": linhas,
    }


@router.post("/rematricula")
def rematricular(body: RematriculaIn, ctx: Contexto = Depends(equipe)):
    """Aplica a rematrícula em lote, tudo ou nada. Notas e frequência do ano anterior permanecem intactos."""
    origem = turma_visivel(ctx, body.turma_origem_id)
    ano_origem, ano_destino = _ano(ctx, origem.ano_letivo_id), _ano(ctx, body.ano_destino_id)
    if ano_destino.ano <= ano_origem.ano:
        raise HTTPException(422, "O ano de destino precisa ser posterior ao da turma.")
    matriculas = {m.aluno_id: m for m in ctx.db.scalars(select(Matricula).where(Matricula.turma_id == origem.id))}
    destinos = {t.id for t in ctx.db.scalars(select(Turma).where(Turma.ano_letivo_id == ano_destino.id))}
    ja = set(ctx.db.scalars(select(Matricula.aluno_id).where(Matricula.ano_letivo_id == ano_destino.id)))
    vistos: set[uuid.UUID] = set()
    for it in body.itens:
        aluno = ctx.db.get(Aluno, it.aluno_id)
        nome = f"{aluno.nome} {aluno.sobrenome}" if aluno else str(it.aluno_id)
        if it.aluno_id not in matriculas or it.aluno_id in vistos:
            raise HTTPException(422, f"{nome}: não está nesta turma (ou foi informado duas vezes).")
        vistos.add(it.aluno_id)
        if it.aluno_id in ja:
            raise HTTPException(409, f"{nome}: já está matriculado no ano de destino.")
        segue = it.resultado in (Resultado.aprovado, Resultado.retido)
        if segue and it.turma_destino_id not in destinos:
            raise HTTPException(422, f"{nome}: escolha uma turma do ano de destino.")
        if not segue and it.turma_destino_id:
            raise HTTPException(422, f"{nome}: transferido ou concluinte não tem turma de destino.")
    agora = datetime.now(UTC)
    for it in body.itens:
        m = matriculas[it.aluno_id]
        aluno = ctx.db.get(Aluno, it.aluno_id)
        assert aluno is not None
        m.situacao = "concluido" if it.resultado == Resultado.concluiu else it.resultado.value
        if it.resultado in (Resultado.aprovado, Resultado.retido):
            ctx.db.add(
                Matricula(
                    escola_id=ctx.escola_id,
                    aluno_id=aluno.id,
                    turma_id=it.turma_destino_id,
                    ano_letivo_id=ano_destino.id,
                )
            )
        elif it.resultado == Resultado.transferido:
            aluno.situacao = SituacaoAluno.transferido
        else:
            aluno.situacao = SituacaoAluno.concluiu
        registrar(
            ctx.db,
            "rematricula",
            escola_id=ctx.escola_id,
            usuario_id=ctx.usuario.id,
            entidade="aluno",
            entidade_id=aluno.id,
            detalhes={
                "resultado": it.resultado.value,
                "de": str(origem.id),
                "para": str(it.turma_destino_id) if it.turma_destino_id else None,
                "em": agora.isoformat(),
            },
        )
    resumo = {r.value: sum(1 for i in body.itens if i.resultado == r) for r in Resultado}
    return {"processados": len(body.itens), **resumo}


# --- Linha do tempo -------------------------------------------------------------------------------------------


def anos_do_aluno(ctx: Contexto, aluno: Aluno, detalhado: bool = True) -> list[dict]:
    """Um item por ano letivo em que o aluno esteve matriculado (turma, resultado e, se pedido, médias e frequência)."""
    anos = []
    rows = ctx.db.execute(
        select(Matricula, AnoLetivo)
        .join(AnoLetivo, AnoLetivo.id == Matricula.ano_letivo_id)
        .where(Matricula.aluno_id == aluno.id)
        .order_by(AnoLetivo.ano)
    ).all()
    for m, ano in rows:
        item = {
            "ano": ano.ano,
            "ano_letivo_id": ano.id,
            "encerrado": not ano.aberto,
            "turma": m.turma.nome,
            "serie": m.turma.serie,
            "situacao": m.situacao,
        }
        if detalhado:
            b = monta_boletim(ctx, aluno, ano)
            item["frequencia_geral"] = b.get("frequencia_geral")
            item["disciplinas"] = [
                {
                    "disciplina": d["disciplina"],
                    "media_anual": d["media_anual"],
                    "frequencia": d["frequencia"],
                    "situacao": d["situacao"],
                }
                for d in b.get("disciplinas", [])
            ]
        anos.append(item)
    return anos


@router.get("/alunos/{aluno_id}/linha-do-tempo")
def linha_do_tempo(aluno_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    """Um item por ano: turma, resultado e, para quem pode ver notas, médias finais e frequência de cada disciplina.

    Professores veem só turma e resultado (as notas de outros professores não são deles). Família e aluno veem
    apenas o que foi publicado, como no boletim.
    """
    aluno = aluno_visivel(ctx, aluno_id)
    detalhado = ctx.papel != Papel.professor
    anos = anos_do_aluno(ctx, aluno, detalhado)
    return {
        "aluno": {"id": aluno.id, "nome": f"{aluno.nome} {aluno.sobrenome}", "situacao": aluno.situacao},
        "anos": anos,
        "notas_visiveis": detalhado,
        "so_publicadas": ctx.papel in (Papel.responsavel, Papel.aluno),
        "equipe": ctx.papel in STAFF,
    }
