"""Conteúdo e layout do histórico escolar em PDF (sem notas de ocorrência, anotações nem dados de saúde)."""

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal

from app.pdfmin import Documento

SITUACAO = {
    "cursando": "Cursando",
    "aprovado": "Aprovado",
    "retido": "Retido",
    "transferido": "Transferido",
    "concluido": "Concluiu",
    "concluiu": "Concluiu",
    "reprovado": "Reprovado",
    "reprovado_por_falta": "Reprovado por falta",
    "abaixo_da_media": "Abaixo da média",
    "ativo": "Matriculado",
    "arquivado": "Arquivado",
}


def num(v, casas: int = 1) -> str:
    if v is None:
        return "—"
    return f"{Decimal(str(v)):.{casas}f}".replace(".", ",")


def dados_do_historico(escola, aluno, anos: list[dict]) -> dict:
    """Só o que entra no PDF, em forma simples e estável (o hash do conteúdo sai daqui)."""
    return {
        "escola": {"nome": escola.nome, "cnpj": escola.cnpj, "cidade": escola.cidade, "uf": escola.uf},
        "aluno": {
            "nome": f"{aluno.nome} {aluno.sobrenome}",
            "nome_social": aluno.nome_social,
            "nascimento": aluno.data_nascimento.isoformat(),
            "ra": aluno.ra,
            "situacao": str(aluno.situacao.value if hasattr(aluno.situacao, "value") else aluno.situacao),
        },
        "anos": [
            {
                "ano": a["ano"],
                "turma": a["turma"],
                "serie": a["serie"],
                "situacao": a["situacao"],
                "encerrado": a["encerrado"],
                "frequencia_geral": None if a.get("frequencia_geral") is None else str(a["frequencia_geral"]),
                "disciplinas": [
                    {
                        "disciplina": d["disciplina"],
                        "media": None if d["media_anual"] is None else str(d["media_anual"]),
                        "frequencia": None if d["frequencia"] is None else str(d["frequencia"]),
                        "situacao": d["situacao"],
                    }
                    for d in a.get("disciplinas", [])
                ],
            }
            for a in anos
        ],
    }


def resumo_sha256(dados: dict) -> str:
    return hashlib.sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def renderiza(
    dados: dict, *, codigo: str, emitido_por: str, url_verificacao: str, quando: datetime | None = None
) -> bytes:
    quando = quando or datetime.now(UTC)
    e, a = dados["escola"], dados["aluno"]
    d = Documento(f"Histórico escolar — {a['nome']}", f"Código de verificação {codigo} · {url_verificacao}")
    d.paragrafo(e["nome"], 12, True, centro=True, entre=2)
    local = " · ".join(
        x for x in (f"CNPJ {e['cnpj']}" if e["cnpj"] else "", ", ".join(x for x in (e["cidade"], e["uf"]) if x)) if x
    )
    if local:
        d.paragrafo(local, 9, cinza=0.35, centro=True, entre=2)
    d.espaco(6)
    d.paragrafo("HISTÓRICO ESCOLAR", 17, True, centro=True, entre=4)
    d.regua(2, 8)
    nasc = date.fromisoformat(a["nascimento"]).strftime("%d/%m/%Y")
    itens = [("Aluno:", a["nome"])]
    if a["nome_social"]:
        itens.append(("Nome social:", a["nome_social"]))
    itens += [("Data de nascimento:", nasc)]
    if a["ra"]:
        itens.append(("RA:", a["ra"]))
    itens.append(("Situação atual:", SITUACAO.get(a["situacao"], a["situacao"])))
    d.pares(itens, 10)
    if not dados["anos"]:
        d.espaco(10)
        d.paragrafo("Nenhuma matrícula registrada.", 10, cinza=0.35)
    for ano in dados["anos"]:
        d.espaco(12)
        d.garante(60)
        resultado = SITUACAO.get(ano["situacao"], ano["situacao"])
        andamento = " · ano em andamento" if ano["situacao"] == "cursando" else ""
        d.paragrafo(f"{ano['ano']} · {ano['turma']} ({ano['serie']}) · {resultado}{andamento}", 11, True, entre=4)
        if ano["disciplinas"]:
            d.tabela(
                [("Disciplina", 215, "e"), ("Média final", 85, "d"), ("Frequência", 90, "d"), ("Resultado", 105, "e")],
                [
                    [
                        x["disciplina"],
                        num(x["media"]),
                        "—" if x["frequencia"] is None else f"{num(x['frequencia'])}%",
                        SITUACAO.get(x["situacao"], x["situacao"]),
                    ]
                    for x in ano["disciplinas"]
                ],
            )
            if ano["frequencia_geral"] is not None:
                d.espaco(3)
                d.paragrafo(f"Frequência geral no ano: {num(ano['frequencia_geral'])}%", 9, cinza=0.25)
        else:
            d.paragrafo("Sem notas ou aulas registradas neste ano.", 9, cinza=0.35)
    d.espaco(26)
    d.garante(110)
    for rotulo in ("Local e data", "Assinatura e carimbo da secretaria"):
        d.espaco(20)
        d.linha(d.m, d.y, d.m + 230, d.y, 0.6, 0.3)
        d.paragrafo(rotulo, 8, cinza=0.35, entre=2)
    d.espaco(10)
    d.regua(2, 6)
    emissao = quando.astimezone().strftime("%d/%m/%Y %H:%M")
    d.paragrafo(
        f"Documento gerado pela plataforma Caderneta em {emissao} por {emitido_por}. "
        "Informativo: só vale como histórico oficial depois de conferido, assinado e carimbado pela secretaria "
        "da escola. Notas e frequência refletem os registros da escola na data da emissão. A autenticidade do "
        "código pode ser conferida no endereço do rodapé.",
        8,
        cinza=0.3,
    )
    return d.bytes(quando)
