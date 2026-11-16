"""Ficha do aluno, responsáveis, ficha de saúde (criptografada e auditada) e matrícula."""

import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.audit import registrar
from app.deps import (
    Contexto,
    aluno_visivel,
    com_perfil,
    equipe_ou_professor,
    exige,
    ids_alunos_visiveis,
    ip_de,
    so_admin,
)
from app.models import (
    STAFF,
    Aluno,
    Convite,
    FichaSaude,
    Matricula,
    Papel,
    SituacaoAluno,
    Turma,
    VinculoResponsavel,
)
from app.routers.convites import cria_convite
from app.routers.escola import ano_atual
from app.security import cifra, cifra_json, decifra, decifra_json

router = APIRouter(tags=["alunos"])

TIPOS_VINCULO = ("mae", "pai", "tutor", "avo", "outro")


class AlunoIn(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    sobrenome: str = Field(min_length=1, max_length=120)
    nome_social: str | None = Field(default=None, max_length=120)
    data_nascimento: date
    ra: str | None = Field(default=None, max_length=30)
    cpf: str | None = Field(default=None, pattern=r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$")
    turma_id: uuid.UUID | None = None


class AlunoPatch(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    sobrenome: str | None = Field(default=None, min_length=1, max_length=120)
    nome_social: str | None = Field(default=None, max_length=120)
    data_nascimento: date | None = None
    ra: str | None = Field(default=None, max_length=30)
    cpf: str | None = Field(default=None, pattern=r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$")
    situacao: SituacaoAluno | None = None


class VinculoIn(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    tipo: str = Field(pattern="^(" + "|".join(TIPOS_VINCULO) + ")$")
    telefone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    pode_buscar: bool = True
    recebe_avisos: bool = True
    emergencia: bool = False
    restrito: bool = False


class ContatoPatch(BaseModel):
    """O próprio responsável só atualiza telefone e e-mail."""

    telefone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None


class SaudeIn(BaseModel):
    alergias: str = Field(default="", max_length=2000)
    medicamentos: str = Field(default="", max_length=2000)
    condicoes: str = Field(default="", max_length=2000)
    restricoes_alimentares: str = Field(default="", max_length=2000)
    necessidades_especificas: str = Field(default="", max_length=2000)
    plano_saude: str = Field(default="", max_length=200)
    observacoes: str = Field(default="", max_length=4000)
    alerta: str = Field(default="", max_length=300, description="Resumo que os professores veem")


class MatriculaIn(BaseModel):
    turma_id: uuid.UUID


def matricula_atual(ctx: Contexto, aluno_id: uuid.UUID) -> Matricula | None:
    ano = ano_atual(ctx)
    if not ano:
        return None
    return ctx.db.scalar(select(Matricula).where(Matricula.aluno_id == aluno_id, Matricula.ano_letivo_id == ano.id))


def matricula(ctx: Contexto, aluno: Aluno, turma_id: uuid.UUID) -> Matricula:
    turma = ctx.db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada.")
    m = ctx.db.scalar(
        select(Matricula).where(Matricula.aluno_id == aluno.id, Matricula.ano_letivo_id == turma.ano_letivo_id)
    )
    if m:
        m.turma_id = turma.id
        m.turma = turma
    else:
        m = Matricula(escola_id=ctx.escola_id, aluno_id=aluno.id, turma_id=turma.id, ano_letivo_id=turma.ano_letivo_id)
        m.turma = turma
        ctx.db.add(m)
    return m


def vinculo_out(v: VinculoResponsavel, convite_pendente: bool) -> dict:
    return {
        "id": v.id,
        "nome": v.nome,
        "tipo": v.tipo,
        "telefone": v.telefone,
        "email": v.email,
        "pode_buscar": v.pode_buscar,
        "recebe_avisos": v.recebe_avisos,
        "emergencia": v.emergencia,
        "restrito": v.restrito,
        "tem_conta": v.usuario_id is not None,
        "convite_pendente": convite_pendente,
    }


def aluno_out(a: Aluno, turma: Turma | None = None) -> dict:
    return {
        "id": a.id,
        "nome": a.nome,
        "sobrenome": a.sobrenome,
        "nome_social": a.nome_social,
        "data_nascimento": a.data_nascimento,
        "ra": a.ra,
        "situacao": a.situacao,
        "turma": {"id": turma.id, "nome": turma.nome, "serie": turma.serie} if turma else None,
    }


@router.get("/alunos")
def lista(
    q: str | None = None,
    turma_id: uuid.UUID | None = None,
    situacao: SituacaoAluno | None = SituacaoAluno.ativo,
    ctx: Contexto = Depends(com_perfil),
):
    ano = ano_atual(ctx)
    query = (
        select(Aluno, Turma)
        .outerjoin(Matricula, (Matricula.aluno_id == Aluno.id) & (Matricula.ano_letivo_id == (ano.id if ano else None)))
        .outerjoin(Turma, Turma.id == Matricula.turma_id)
        .order_by(Aluno.nome, Aluno.sobrenome)
        .limit(500)
    )
    if (escopo := ids_alunos_visiveis(ctx)) is not None:
        query = query.where(Aluno.id.in_(escopo))
    if situacao:
        query = query.where(Aluno.situacao == situacao)
    if turma_id:
        query = query.where(Turma.id == turma_id)
    if q:
        # Nome completo ("Lucas Moreira"), nome social ou RA; % e _ digitados não viram curinga.
        limpo = " ".join(q.split()).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        termo = f"%{limpo}%"
        query = query.where(
            or_(
                func.concat_ws(" ", Aluno.nome, Aluno.sobrenome).ilike(termo, escape="\\"),
                func.concat_ws(" ", Aluno.nome_social, Aluno.sobrenome).ilike(termo, escape="\\"),
                Aluno.ra.ilike(termo, escape="\\"),
            )
        )
    return [aluno_out(a, t) for a, t in ctx.db.execute(query).all()]


@router.post("/alunos", status_code=201)
def cria(dados: AlunoIn, request: Request, ctx: Contexto = Depends(so_admin)):
    a = Aluno(escola_id=ctx.escola_id, **dados.model_dump(exclude={"turma_id"}))
    ctx.db.add(a)
    try:
        with ctx.db.begin_nested():
            ctx.db.flush()
    except IntegrityError:
        raise HTTPException(409, "Já existe um aluno com esse RA.") from None
    m = matricula(ctx, a, dados.turma_id) if dados.turma_id else None
    registrar(
        ctx.db,
        "aluno_criado",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="aluno",
        entidade_id=a.id,
        ip=ip_de(request),
    )
    return aluno_out(a, m.turma if m else None)


@router.get("/alunos/{aluno_id}")
def detalhe(aluno_id: uuid.UUID, ctx: Contexto = Depends(com_perfil)):
    a = aluno_visivel(ctx, aluno_id)
    m = matricula_atual(ctx, a.id)
    out = aluno_out(a, m.turma if m else None)
    if ctx.papel in STAFF:
        out["cpf"] = a.cpf
        out["historico"] = [
            {"ano_letivo_id": h.ano_letivo_id, "turma": h.turma.nome, "serie": h.turma.serie, "situacao": h.situacao}
            for h in ctx.db.scalars(select(Matricula).where(Matricula.aluno_id == a.id))
        ]
    vinculos = list(ctx.db.scalars(select(VinculoResponsavel).where(VinculoResponsavel.aluno_id == a.id)))
    if ctx.papel != Papel.aluno:
        pend = set(
            ctx.db.scalars(
                select(Convite.vinculo_id).where(
                    Convite.aluno_id == a.id, Convite.aceito_em.is_(None), Convite.revogado.is_(False)
                )
            )
        )
        visiveis = [v for v in vinculos if ctx.papel in STAFF or not v.restrito]
        out["responsaveis"] = [vinculo_out(v, v.id in pend) for v in visiveis]
    ficha = ctx.db.get(FichaSaude, a.id)
    out["tem_alerta_saude"] = bool(ficha and ficha.alerta_enc)
    out["aluno_tem_conta"] = a.usuario_id is not None
    return out


@router.patch("/alunos/{aluno_id}")
def edita(aluno_id: uuid.UUID, dados: AlunoPatch, request: Request, ctx: Contexto = Depends(so_admin)):
    a = aluno_visivel(ctx, aluno_id)
    mudou = dados.model_dump(exclude_unset=True)
    for k, v in mudou.items():
        setattr(a, k, v)
    registrar(
        ctx.db,
        "aluno_editado",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="aluno",
        entidade_id=a.id,
        detalhes={"campos": sorted(mudou)},
        ip=ip_de(request),
    )
    return aluno_out(a)


@router.put("/alunos/{aluno_id}/matricula")
def muda_matricula(aluno_id: uuid.UUID, dados: MatriculaIn, ctx: Contexto = Depends(so_admin)):
    a = aluno_visivel(ctx, aluno_id)
    m = matricula(ctx, a, dados.turma_id)
    ctx.db.flush()
    return {"turma": {"id": m.turma_id}}


# --- Responsáveis ---------------------------------------------------------------------------------------


@router.post("/alunos/{aluno_id}/responsaveis", status_code=201)
def adiciona_responsavel(aluno_id: uuid.UUID, dados: VinculoIn, ctx: Contexto = Depends(so_admin)):
    a = aluno_visivel(ctx, aluno_id)
    v = VinculoResponsavel(escola_id=ctx.escola_id, aluno_id=a.id, **dados.model_dump())
    ctx.db.add(v)
    ctx.db.flush()
    return vinculo_out(v, False)


@router.patch("/responsaveis/{vinculo_id}")
def edita_responsavel(
    vinculo_id: uuid.UUID, dados: dict, request: Request, ctx: Contexto = Depends(exige(Papel.admin, Papel.responsavel))
):
    v = ctx.db.get(VinculoResponsavel, vinculo_id)
    if not v:
        raise HTTPException(404, "Responsável não encontrado.")
    if ctx.papel == Papel.responsavel:
        if v.usuario_id != ctx.usuario.id:
            raise HTTPException(404, "Responsável não encontrado.")
        novos = ContatoPatch.model_validate(dados).model_dump(exclude_unset=True)
    else:
        novos = VinculoIn.model_validate({**vinculo_out(v, False), **dados}).model_dump()
    for k, val in novos.items():
        setattr(v, k, val)
    registrar(
        ctx.db,
        "responsavel_editado",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="vinculo",
        entidade_id=v.id,
        detalhes={"campos": sorted(novos)},
        ip=ip_de(request),
    )
    return vinculo_out(v, False)


@router.delete("/responsaveis/{vinculo_id}", status_code=204)
def remove_responsavel(vinculo_id: uuid.UUID, ctx: Contexto = Depends(so_admin)):
    v = ctx.db.get(VinculoResponsavel, vinculo_id)
    if not v:
        raise HTTPException(404, "Responsável não encontrado.")
    ctx.db.delete(v)


@router.post("/responsaveis/{vinculo_id}/convite", status_code=201)
def convida_responsavel(vinculo_id: uuid.UUID, ctx: Contexto = Depends(so_admin)):
    v = ctx.db.get(VinculoResponsavel, vinculo_id)
    if not v:
        raise HTTPException(404, "Responsável não encontrado.")
    if not v.email:
        raise HTTPException(422, "Cadastre um e-mail para enviar o convite.")
    if v.usuario_id:
        raise HTTPException(409, "Esse responsável já tem acesso.")
    for antigo in ctx.db.scalars(select(Convite).where(Convite.vinculo_id == v.id, Convite.aceito_em.is_(None))):
        antigo.revogado = True
    link = cria_convite(
        ctx.db,
        escola_id=ctx.escola_id,
        email=v.email,
        nome=v.nome,
        papel=Papel.responsavel,
        criado_por=ctx.usuario.id,
        vinculo_id=v.id,
        aluno_id=v.aluno_id,
    )
    return {"link": link}


class ConviteAlunoIn(BaseModel):
    email: EmailStr


@router.post("/alunos/{aluno_id}/convite", status_code=201)
def convida_aluno(aluno_id: uuid.UUID, dados: ConviteAlunoIn, ctx: Contexto = Depends(so_admin)):
    a = aluno_visivel(ctx, aluno_id)
    if a.usuario_id:
        raise HTTPException(409, "O aluno já tem acesso.")
    link = cria_convite(
        ctx.db,
        escola_id=ctx.escola_id,
        email=dados.email,
        nome=a.nome_social or a.nome,
        papel=Papel.aluno,
        criado_por=ctx.usuario.id,
        aluno_id=a.id,
    )
    return {"link": link}


# --- Saúde (dado sensível) -------------------------------------------------------------------------------


@router.get("/alunos/{aluno_id}/saude")
def ve_saude(aluno_id: uuid.UUID, request: Request, ctx: Contexto = Depends(com_perfil)):
    if ctx.papel == Papel.aluno:
        raise HTTPException(403, "Sem permissão para esta ação.")
    a = aluno_visivel(ctx, aluno_id)
    ficha = ctx.db.get(FichaSaude, a.id)
    alerta = decifra(ficha.alerta_enc, f"alerta:{a.id}") if ficha and ficha.alerta_enc else ""
    if ctx.papel == Papel.professor:
        # Professores veem só o alerta resumido definido pela escola.
        return {"alerta": alerta}
    registrar(
        ctx.db,
        "saude_lida",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="aluno",
        entidade_id=a.id,
        ip=ip_de(request),
    )
    dados = decifra_json(ficha.dados_enc, str(a.id)) if ficha else SaudeIn().model_dump(exclude={"alerta"})
    return {**dados, "alerta": alerta, "atualizado_em": ficha.atualizado_em if ficha else None}


@router.put("/alunos/{aluno_id}/saude")
def grava_saude(
    aluno_id: uuid.UUID,
    dados: SaudeIn,
    request: Request,
    ctx: Contexto = Depends(exige(Papel.admin, Papel.responsavel)),
):
    a = aluno_visivel(ctx, aluno_id)
    ficha = ctx.db.get(FichaSaude, a.id)
    conteudo = dados.model_dump(exclude={"alerta"})
    if ctx.papel == Papel.responsavel and ficha and ficha.alerta_enc:
        alerta = decifra(ficha.alerta_enc, f"alerta:{a.id}")  # o alerta para professores é definido pela escola
    else:
        alerta = dados.alerta.strip()
    if not ficha:
        ficha = FichaSaude(aluno_id=a.id, escola_id=ctx.escola_id, dados_enc=b"")
        ctx.db.add(ficha)
    ficha.dados_enc = cifra_json(conteudo, str(a.id))
    ficha.alerta_enc = cifra(alerta, f"alerta:{a.id}") if alerta else None
    ficha.atualizado_por = ctx.usuario.id
    ficha.atualizado_em = datetime.now(UTC)
    registrar(
        ctx.db,
        "saude_editada",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="aluno",
        entidade_id=a.id,
        ip=ip_de(request),
    )
    return {"ok": True}


@router.get("/turmas/{turma_id}/alertas-saude")
def alertas_turma(turma_id: uuid.UUID, ctx: Contexto = Depends(equipe_ou_professor)):
    """Lista de alertas essenciais da turma (ex.: alergias graves) para quem está em sala."""
    from app.routers.turmas import turma_visivel

    t = turma_visivel(ctx, turma_id)
    rows = ctx.db.execute(
        select(Aluno, FichaSaude)
        .join(Matricula, Matricula.aluno_id == Aluno.id)
        .join(FichaSaude, FichaSaude.aluno_id == Aluno.id)
        .where(Matricula.turma_id == t.id, FichaSaude.alerta_enc.is_not(None))
        .order_by(Aluno.nome)
    ).all()
    return [
        {
            "aluno_id": a.id,
            "nome": f"{a.nome_social or a.nome} {a.sobrenome}",
            "alerta": decifra(f.alerta_enc, f"alerta:{a.id}"),
        }
        for a, f in rows
    ]
