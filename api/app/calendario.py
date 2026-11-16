"""Regras puras do calendário: feriados nacionais, bloqueio de aula e texto iCal."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import BLOQUEIA_AULA, Evento


def pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo gregoriano de Meeus/Jones/Butcher)."""
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    j = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * j) // 451
    mes = (h + j - 7 * m + 114) // 31
    dia = (h + j - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


FAC = "Ponto facultativo"


def feriados_sugeridos(ano: int) -> list[dict]:
    """Feriados nacionais por lei e datas comuns no calendário escolar.

    `nacional=True`: feriado nacional em lei federal (Lei 662/1949 com a redação da Lei 10.607/2002,
    Lei 6.802/1980 para 12/10 e Lei 14.759/2023 para 20/11). `nacional=False`: data que a escola decide
    (Sexta-feira da Paixão, feriado religioso pela Lei 9.093/1995; Carnaval e Corpus Christi, pontos facultativos).
    """
    p = pascoa(ano)
    fixos = [
        (date(ano, 1, 1), "Confraternização Universal", "Lei 662/1949"),
        (date(ano, 4, 21), "Tiradentes", "Lei 662/1949"),
        (date(ano, 5, 1), "Dia do Trabalho", "Lei 662/1949"),
        (date(ano, 9, 7), "Independência do Brasil", "Lei 662/1949"),
        (date(ano, 10, 12), "Nossa Senhora Aparecida", "Lei 6.802/1980"),
        (date(ano, 11, 2), "Finados", "Lei 662/1949"),
        (date(ano, 11, 15), "Proclamação da República", "Lei 662/1949"),
        (date(ano, 11, 20), "Consciência Negra", "Lei 14.759/2023"),
        (date(ano, 12, 25), "Natal", "Lei 662/1949"),
    ]
    out = [{"data": d, "nome": n, "nacional": True, "base": b} for d, n, b in fixos]
    out += [
        {
            "data": p - timedelta(days=48),
            "nome": "Carnaval (segunda, ponto facultativo)",
            "nacional": False,
            "base": "Ponto facultativo",
        },
        {
            "data": p - timedelta(days=47),
            "nome": "Carnaval (terça, ponto facultativo)",
            "nacional": False,
            "base": "Ponto facultativo",
        },
        {"data": p - timedelta(days=2), "nome": "Sexta-feira da Paixão", "nacional": False, "base": "Lei 9.093/1995"},
        {
            "data": p + timedelta(days=60),
            "nome": "Corpus Christi (ponto facultativo)",
            "nacional": False,
            "base": "Ponto facultativo",
        },
    ]
    return sorted(out, key=lambda x: x["data"])


def dia_sem_aula(db: Session, escola_id: uuid.UUID, turma_id: uuid.UUID, dia: date) -> Evento | None:
    """Feriado ou dia sem aula que vale para a turma (da escola toda ou só dela) nessa data."""
    return db.scalars(
        select(Evento)
        .where(
            Evento.escola_id == escola_id,
            Evento.tipo.in_(list(BLOQUEIA_AULA)),
            Evento.inicio <= dia,
            Evento.fim >= dia,
            or_(Evento.turma_id.is_(None), Evento.turma_id == turma_id),
        )
        .limit(1)
    ).first()


# --- iCal (RFC 5545) --------------------------------------------------------------------------------------


def _esc(t: str) -> str:
    t = t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return t.replace("\r", "").replace("\n", "\\n")


def _dobra(linha: str) -> str:
    """Linhas com mais de 75 octetos continuam na seguinte, começando por espaço."""
    b = linha.encode()
    if len(b) <= 75:
        return linha
    partes, atual = [], ""
    for ch in linha:
        if len((atual + ch).encode()) > (75 if not partes else 74):
            partes.append(atual)
            atual = ch
        else:
            atual += ch
    partes.append(atual)
    return "\r\n ".join(partes)


def ics(nome: str, itens: list[dict], agora: datetime | None = None) -> str:
    """Calendário de eventos de dia inteiro. Cada item: id, titulo, descricao, inicio, fim (inclusivo)."""
    carimbo = (agora or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Caderneta//Calendario//PT-BR",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_esc(nome)}",
        "X-WR-TIMEZONE:America/Sao_Paulo",
    ]
    for i in itens:
        linhas += [
            "BEGIN:VEVENT",
            f"UID:{i['id']}@caderneta",
            f"DTSTAMP:{carimbo}",
            f"DTSTART;VALUE=DATE:{i['inicio']:%Y%m%d}",
            f"DTEND;VALUE=DATE:{i['fim'] + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_esc(i['titulo'])}",
        ]
        if i.get("descricao"):
            linhas.append(f"DESCRIPTION:{_esc(i['descricao'])}")
        linhas.append("END:VEVENT")
    linhas.append("END:VCALENDAR")
    return "\r\n".join(_dobra(x) for x in linhas) + "\r\n"
