"""Importação de alunos e responsáveis por planilha CSV: pré-visualização e gravação tudo-ou-nada."""

import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.audit import registrar
from app.config import get_settings
from app.deps import Contexto, ip_de, so_admin
from app.models import Aluno, Papel, Turma, VinculoResponsavel
from app.routers.alunos import TIPOS_VINCULO, matricula
from app.routers.convites import cria_convite
from app.routers.escola import ano_atual

router = APIRouter(prefix="/importacao", tags=["importacao"])

COLUNAS = [
    "nome",
    "sobrenome",
    "data_nascimento",
    "ra",
    "turma",
    "responsavel1_nome",
    "responsavel1_tipo",
    "responsavel1_email",
    "responsavel1_telefone",
    "responsavel2_nome",
    "responsavel2_tipo",
    "responsavel2_email",
    "responsavel2_telefone",
]
OBRIGATORIAS = ["nome", "sobrenome", "data_nascimento", "turma"]
EXEMPLO = [
    "Ana",
    "Souza",
    "14/03/2013",
    "2026001",
    "7º A",
    "Carla Souza",
    "mae",
    "carla@example.com",
    "(11) 98888-0000",
    "",
    "",
    "",
    "",
]
_email = TypeAdapter(EmailStr)


def _texto(conteudo: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252"):  # Excel no Brasil costuma salvar em Windows-1252
        try:
            return conteudo.decode(enc)
        except UnicodeDecodeError:
            continue
    raise HTTPException(422, "Não foi possível ler o arquivo. Salve como CSV (UTF-8).")


def _data(valor: str) -> date:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(valor.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError("data inválida (use dd/mm/aaaa)")


def _le(conteudo: bytes) -> list[dict[str, str]]:
    texto = _texto(conteudo)
    primeira = texto.splitlines()[0] if texto else ""
    delim = ";" if primeira.count(";") > primeira.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=delim)
    cab = [c.strip().lower() for c in (leitor.fieldnames or [])]
    faltando = [c for c in OBRIGATORIAS if c not in cab]
    if faltando:
        raise HTTPException(422, f"Colunas obrigatórias ausentes: {', '.join(faltando)}. Baixe o modelo.")
    linhas = []
    for row in leitor:
        limpo = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        if any(limpo.values()):
            linhas.append(limpo)
    if len(linhas) > 2000:
        raise HTTPException(422, "Máximo de 2000 alunos por arquivo.")
    return linhas


def _valida(ctx: Contexto, linhas: list[dict[str, str]]):
    ano = ano_atual(ctx)
    if not ano:
        raise HTTPException(409, "Crie o ano letivo e as turmas antes de importar.")
    turmas = {t.nome.lower(): t for t in ctx.db.scalars(select(Turma).where(Turma.ano_letivo_id == ano.id))}
    ras_existentes = set(ctx.db.scalars(select(Aluno.ra).where(Aluno.ra.is_not(None))))
    ras_arquivo: set[str] = set()
    erros, validas = [], []
    for n, ln in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        e: list[dict] = []

        def erro(campo: str, msg: str, n: int = n, e: list[dict] = e) -> None:
            e.append({"linha": n, "campo": campo, "mensagem": msg})

        for c in OBRIGATORIAS:
            if not ln.get(c):
                erro(c, "obrigatório")
        nasc = None
        if ln.get("data_nascimento"):
            try:
                nasc = _data(ln["data_nascimento"])
                if not date(1990, 1, 1) <= nasc <= date.today():
                    erro("data_nascimento", "fora do intervalo esperado")
            except ValueError as ex:
                erro("data_nascimento", str(ex))
        turma = turmas.get(ln.get("turma", "").lower())
        if ln.get("turma") and not turma:
            erro("turma", f"turma '{ln['turma']}' não existe no ano {ano.ano}")
        ra = ln.get("ra") or None
        if ra:
            if ra in ras_existentes:
                erro("ra", "já cadastrado")
            elif ra in ras_arquivo:
                erro("ra", "repetido no arquivo")
            ras_arquivo.add(ra)
        resps = []
        for i in (1, 2):
            p = f"responsavel{i}_"
            nome = ln.get(p + "nome", "")
            if not nome:
                continue
            tipo = (ln.get(p + "tipo") or "outro").lower()
            if tipo not in TIPOS_VINCULO:
                erro(p + "tipo", f"use {', '.join(TIPOS_VINCULO)}")
            email = ln.get(p + "email") or None
            if email:
                try:
                    email = _email.validate_python(email)
                except ValidationError:
                    erro(p + "email", "e-mail inválido")
            resps.append(
                {
                    "nome": nome,
                    "tipo": tipo,
                    "email": email,
                    "telefone": ln.get(p + "telefone") or None,
                    "emergencia": i == 1,
                }
            )
        if e:
            erros.extend(e)
        else:
            validas.append(
                {
                    "nome": ln["nome"],
                    "sobrenome": ln["sobrenome"],
                    "data_nascimento": nasc,
                    "ra": ra,
                    "turma": turma,
                    "responsaveis": resps,
                }
            )
    return validas, erros


@router.get("/modelo.csv")
def modelo(_: Contexto = Depends(so_admin)):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(COLUNAS)
    w.writerow(EXEMPLO)
    return Response(
        "﻿" + buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="modelo-alunos.csv"'},
    )


@router.post("/alunos")
async def importa(
    request: Request,
    arquivo: UploadFile = File(...),
    confirmar: bool = Form(False),
    enviar_convites: bool = Form(False),
    ctx: Contexto = Depends(so_admin),
):
    conteudo = await arquivo.read(get_settings().max_upload_bytes + 1)
    if len(conteudo) > get_settings().max_upload_bytes:
        raise HTTPException(413, "Arquivo grande demais (máx. 2 MB).")
    validas, erros = _valida(ctx, _le(conteudo))
    previa = [
        {
            "nome": v["nome"],
            "sobrenome": v["sobrenome"],
            "data_nascimento": v["data_nascimento"],
            "ra": v["ra"],
            "turma": v["turma"].nome,
            "responsaveis": [r["nome"] for r in v["responsaveis"]],
        }
        for v in validas
    ]
    if not confirmar or erros:
        return {"previa": previa, "erros": erros, "importados": 0}

    convites = 0
    for v in validas:
        a = Aluno(
            escola_id=ctx.escola_id,
            nome=v["nome"],
            sobrenome=v["sobrenome"],
            data_nascimento=v["data_nascimento"],
            ra=v["ra"],
        )
        ctx.db.add(a)
        ctx.db.flush()
        matricula(ctx, a, v["turma"].id)
        for r in v["responsaveis"]:
            vin = VinculoResponsavel(escola_id=ctx.escola_id, aluno_id=a.id, **r)
            ctx.db.add(vin)
            ctx.db.flush()
            if enviar_convites and r["email"]:
                cria_convite(
                    ctx.db,
                    escola_id=ctx.escola_id,
                    email=r["email"],
                    nome=r["nome"],
                    papel=Papel.responsavel,
                    criado_por=ctx.usuario.id,
                    vinculo_id=vin.id,
                    aluno_id=a.id,
                )
                convites += 1
    registrar(
        ctx.db,
        "importacao_alunos",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        detalhes={"alunos": len(validas), "convites": convites},
        ip=ip_de(request),
    )
    return {"previa": previa, "erros": [], "importados": len(validas), "convites": convites}
