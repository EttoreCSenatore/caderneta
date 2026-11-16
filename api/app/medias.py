"""Motor de médias: funções puras (sem banco), cobertas por testes de tabela.

Convenções:
- Toda nota é convertida para a escala da regra (ex.: 0 a 10) antes de qualquer conta.
- Notas `dispensada` e `falta_justificada` não entram na conta; notas em branco contam como pendentes.
- A recuperação é uma avaliação marcada como tal dentro do período e age conforme a regra.
- Falta justificada continua sendo falta para o cálculo de frequência (a LDB só abona casos especiais);
  ela aparece separada para a escola acompanhar.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.models import Arredondamento, Recuperacao, StatusNota, TipoMedia

CEM = Decimal(100)


@dataclass(frozen=True)
class Regra:
    tipo_media: TipoMedia = TipoMedia.ponderada
    pesos_periodos: tuple[Decimal, ...] | None = None
    recuperacao: Recuperacao = Recuperacao.substitui_se_maior
    arredondamento: Arredondamento = Arredondamento.decimo
    nota_maxima: Decimal = Decimal(10)
    media_aprovacao: Decimal = Decimal(6)
    frequencia_minima: int = 75


@dataclass(frozen=True)
class NotaLancada:
    valor: Decimal | None
    peso: Decimal = Decimal(1)
    nota_maxima: Decimal = Decimal(10)
    status: StatusNota = StatusNota.normal
    recuperacao: bool = False


@dataclass(frozen=True)
class ResultadoPeriodo:
    media: Decimal | None
    media_antes_recuperacao: Decimal | None
    recuperacao_aplicada: bool
    pendentes: int


@dataclass(frozen=True)
class ResultadoAnual:
    media: Decimal | None
    completa: bool


def arredonda(valor: Decimal, modo: Arredondamento) -> Decimal:
    if modo == Arredondamento.meio:
        return (valor * 2).quantize(Decimal(1), ROUND_HALF_UP) / 2
    if modo == Arredondamento.decimo:
        return valor.quantize(Decimal("0.1"), ROUND_HALF_UP)
    return valor.quantize(Decimal("0.01"), ROUND_HALF_UP)


def na_escala(n: NotaLancada, regra: Regra) -> Decimal:
    assert n.valor is not None
    return n.valor * regra.nota_maxima / n.nota_maxima


def _conta(n: NotaLancada) -> bool:
    return n.status == StatusNota.normal and n.valor is not None


def media_periodo(notas: Sequence[NotaLancada], regra: Regra) -> ResultadoPeriodo:
    regulares = [n for n in notas if not n.recuperacao]
    validas = [n for n in regulares if _conta(n)]
    pendentes = sum(1 for n in notas if n.status == StatusNota.normal and n.valor is None and not n.recuperacao)

    base: Decimal | None = None
    if validas:
        if regra.tipo_media == TipoMedia.ponderada:
            soma_pesos = sum((n.peso for n in validas), Decimal(0))
            if soma_pesos > 0:
                base = sum((na_escala(n, regra) * n.peso for n in validas), Decimal(0)) / soma_pesos
        if base is None:  # aritmética, ou todos os pesos zerados
            base = sum((na_escala(n, regra) for n in validas), Decimal(0)) / len(validas)

    recs = [na_escala(n, regra) for n in notas if n.recuperacao and _conta(n)]
    rec = recs[-1] if recs else None
    media, aplicada = base, False
    if rec is not None and regra.recuperacao != Recuperacao.nenhuma:
        if base is None or regra.recuperacao == Recuperacao.substitui_se_maior and rec > base:
            media, aplicada = rec, True
        elif regra.recuperacao == Recuperacao.media:
            nova = (base + rec) / 2
            if nova > base:  # recuperação nunca abaixa a média
                media, aplicada = nova, True

    def r(v: Decimal | None) -> Decimal | None:
        return None if v is None else arredonda(v, regra.arredondamento)

    return ResultadoPeriodo(r(media), r(base), aplicada, pendentes)


def media_anual(medias: Sequence[Decimal | None], regra: Regra) -> ResultadoAnual:
    """Média dos períodos com nota; `completa` só quando todos os períodos têm média."""
    pesos = list(regra.pesos_periodos) if regra.pesos_periodos and len(regra.pesos_periodos) == len(medias) else None
    pares = [(m, pesos[i] if pesos else Decimal(1)) for i, m in enumerate(medias) if m is not None]
    if not pares:
        return ResultadoAnual(None, False)
    soma_pesos = sum((p for _, p in pares), Decimal(0))
    if soma_pesos == 0:
        return ResultadoAnual(None, False)
    valor = sum((m * p for m, p in pares), Decimal(0)) / soma_pesos
    return ResultadoAnual(arredonda(valor, regra.arredondamento), len(pares) == len(medias))


def frequencia_pct(aulas_dadas: int, faltas: int) -> Decimal | None:
    if aulas_dadas <= 0:
        return None
    return (CEM * (aulas_dadas - faltas) / aulas_dadas).quantize(Decimal("0.1"), ROUND_HALF_UP)


def situacao(anual: ResultadoAnual, freq: Decimal | None, regra: Regra) -> str:
    """cursando | abaixo_da_media | aprovado | reprovado | reprovado_por_falta."""
    if freq is not None and anual.completa and freq < regra.frequencia_minima:
        return "reprovado_por_falta"
    if anual.media is None:
        return "cursando"
    abaixo = anual.media < regra.media_aprovacao
    if not anual.completa:
        return "abaixo_da_media" if abaixo else "cursando"
    return "reprovado" if abaixo else "aprovado"
