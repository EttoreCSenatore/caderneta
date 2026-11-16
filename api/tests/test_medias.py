"""Testes de tabela do motor de médias (sem banco)."""

from decimal import Decimal as D

import pytest

from app.medias import (
    NotaLancada,
    Regra,
    ResultadoAnual,
    arredonda,
    frequencia_pct,
    media_anual,
    media_periodo,
    situacao,
)
from app.models import Arredondamento as A
from app.models import Recuperacao as R
from app.models import StatusNota as S
from app.models import TipoMedia as T


def N(v, peso=1, maxima=10, status=S.normal, rec=False):
    return NotaLancada(None if v is None else D(str(v)), D(str(peso)), D(str(maxima)), status, rec)


@pytest.mark.parametrize(
    "valor, modo, esperado",
    [
        ("6.85", A.decimo, "6.9"),
        ("6.84", A.decimo, "6.8"),
        ("6.75", A.meio, "7.0"),
        ("6.74", A.meio, "6.5"),
        ("6.25", A.meio, "6.5"),
        ("6.24", A.meio, "6.0"),
        ("6.845", A.nenhum, "6.85"),
    ],
)
def test_arredondamento(valor, modo, esperado):
    assert arredonda(D(valor), modo) == D(esperado)


@pytest.mark.parametrize(
    "notas, regra, media, antes, aplicada, pendentes",
    [
        # Exemplo da documentação: ponderada, arredonda para 0,5
        ([N(7, 2), N(9, 1), N("5.5", 2)], Regra(arredondamento=A.meio), "7.0", "7.0", False, 0),
        # Aritmética ignora pesos
        ([N(7, 2), N(9, 1), N("5.5", 2)], Regra(tipo_media=T.aritmetica), "7.2", "7.2", False, 0),
        # Escalas diferentes: 15 de 20 vira 7,5
        ([N(15, 1, 20), N(5)], Regra(), "6.3", "6.3", False, 0),
        # Dispensada e falta justificada não entram; em branco é pendente
        (
            [N(8), N(None), N(2, status=S.dispensada), N(None, status=S.falta_justificada)],
            Regra(),
            "8.0",
            "8.0",
            False,
            1,
        ),
        # Recuperação substitui se maior
        ([N(4), N(5), N(7, rec=True)], Regra(), "7.0", "4.5", True, 0),
        # ... e não abaixa
        ([N(6), N(8), N(3, rec=True)], Regra(), "7.0", "7.0", False, 0),
        # Recuperação pela média entre média e recuperação
        ([N(4), N(8, rec=True)], Regra(recuperacao=R.media), "6.0", "4.0", True, 0),
        # Sem recuperação na regra
        ([N(4), N(9, rec=True)], Regra(recuperacao=R.nenhuma), "4.0", "4.0", False, 0),
        # Só recuperação lançada
        ([N(None), N(6, rec=True)], Regra(), "6.0", None, True, 1),
        # Nada lançado
        ([N(None), N(None)], Regra(), None, None, False, 2),
        # Pesos todos zero caem para aritmética
        ([N(4, 0), N(8, 0)], Regra(), "6.0", "6.0", False, 0),
        # Escala 0 a 100
        ([N(7), N(9)], Regra(nota_maxima=D(100), arredondamento=A.nenhum), "80.00", "80.00", False, 0),
    ],
)
def test_media_periodo(notas, regra, media, antes, aplicada, pendentes):
    r = media_periodo(notas, regra)
    assert r.media == (D(media) if media else None)
    assert r.media_antes_recuperacao == (D(antes) if antes else None)
    assert r.recuperacao_aplicada is aplicada
    assert r.pendentes == pendentes


@pytest.mark.parametrize(
    "medias, pesos, esperado, completa",
    [
        (["6", "7", "8", "9"], None, "7.5", True),
        (["6", "7", "8", "9"], (2, 2, 3, 3), "7.7", True),
        (["6", None, None, None], (2, 2, 3, 3), "6.0", False),
        ([None, None], None, None, False),
        (["5", "7"], (1, 2, 3), "6.0", True),  # pesos com tamanho errado são ignorados
    ],
)
def test_media_anual(medias, pesos, esperado, completa):
    regra = Regra(pesos_periodos=tuple(D(p) for p in pesos) if pesos else None)
    r = media_anual([D(m) if m else None for m in medias], regra)
    assert r == ResultadoAnual(D(esperado) if esperado else None, completa)


def test_frequencia():
    assert frequencia_pct(0, 0) is None
    assert frequencia_pct(80, 20) == D("75.0")
    assert frequencia_pct(3, 1) == D("66.7")


@pytest.mark.parametrize(
    "media, completa, freq, esperado",
    [
        ("7", True, "90", "aprovado"),
        ("5.9", True, "90", "reprovado"),
        ("9", True, "74.9", "reprovado_por_falta"),
        ("5", False, "60", "abaixo_da_media"),  # ano em curso: falta ainda não reprova
        ("8", False, None, "cursando"),
        (None, False, None, "cursando"),
    ],
)
def test_situacao(media, completa, freq, esperado):
    anual = ResultadoAnual(D(media) if media else None, completa)
    assert situacao(anual, D(freq) if freq else None, Regra()) == esperado
