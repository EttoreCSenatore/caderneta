"""Gerador de PDF mínimo, sem dependências: texto em Helvetica, linhas, retângulos e tabelas que quebram de página.

Escrito aqui de propósito: uma biblioteca de PDF a mais seria mais uma licença e mais uma superfície para auditar (M8),
e o histórico escolar só precisa de texto e tabela. Usa as fontes padrão do PDF (Helvetica e Helvetica-Bold, que todo
leitor traz), codificação WinAnsi (cp1252, cobre o português) e as métricas AFM da Helvetica para quebrar linhas.
"""

import unicodedata
from datetime import UTC, datetime

A4 = (595.0, 842.0)

_REG = (
    "278 278 355 556 556 889 667 191 333 333 389 584 278 333 278 278 "
    "556 556 556 556 556 556 556 556 556 556 278 278 584 584 584 556 "
    "1015 667 667 722 722 667 611 778 722 278 500 667 556 833 722 778 "
    "667 778 722 667 611 722 667 944 667 667 611 278 278 278 469 556 "
    "333 556 556 500 556 556 278 556 556 222 222 500 222 833 556 556 "
    "556 556 333 500 278 556 500 722 500 500 500 334 260 334 584"
)
_BOLD = (
    "278 333 474 556 556 889 722 238 333 333 389 584 278 333 278 278 "
    "556 556 556 556 556 556 556 556 556 556 333 333 584 584 584 611 "
    "975 722 722 722 722 667 611 778 722 278 556 722 611 833 722 778 "
    "667 778 722 667 611 722 667 944 667 667 611 333 278 333 584 556 "
    "333 556 611 556 611 556 333 611 611 278 278 556 278 889 611 611 "
    "611 611 389 556 333 611 556 778 556 556 500 389 280 389 584"
)
_W = {False: [int(x) for x in _REG.split()], True: [int(x) for x in _BOLD.split()]}


def _base(ch: str) -> str:
    """Letra sem acento (á vira a) para medir; o glifo acentuado tem a mesma largura da letra base."""
    d = unicodedata.normalize("NFD", ch)
    return d[0] if d else ch


def largura(texto: str, tam: float, negrito: bool = False) -> float:
    tabela = _W[negrito]
    total = 0
    for ch in texto:
        b = _base(ch)
        o = ord(b)
        total += tabela[o - 32] if 32 <= o <= 126 else 556
    return total * tam / 1000


def _pdf_str(texto: str) -> bytes:
    """String PDF em cp1252 com escape de \\, ( e )."""
    b = texto.encode("cp1252", "replace")
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _hex_utf16(texto: str) -> bytes:
    return b"<FEFF" + texto.encode("utf-16-be").hex().upper().encode() + b">"


def quebra(texto: str, max_w: float, tam: float, negrito: bool = False) -> list[str]:
    """Quebra o texto em linhas que cabem em `max_w` pontos."""
    linhas: list[str] = []
    for paragrafo in texto.split("\n"):
        atual = ""
        for palavra in paragrafo.split():
            while largura(palavra, tam, negrito) > max_w:  # palavra maior que a linha: parte em pedaços
                corte = len(palavra) - 1
                while corte > 1 and largura(palavra[:corte], tam, negrito) > max_w:
                    corte -= 1
                if atual:
                    linhas.append(atual)
                    atual = ""
                linhas.append(palavra[:corte])
                palavra = palavra[corte:]
            teste = f"{atual} {palavra}".strip()
            if largura(teste, tam, negrito) <= max_w or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        linhas.append(atual)
    return linhas


class Documento:
    """Fluxo de página única coluna: o cursor desce e a página vira sozinha."""

    def __init__(self, titulo: str, rodape: str = "", margem: float = 50, topo: float = 56, base: float = 56):
        self.titulo, self.rodape = titulo, rodape
        self.m, self.topo, self.base = margem, topo, base
        self.larg, self.alt = A4
        self.paginas: list[list[bytes]] = []
        self.y = 0.0
        self._nova_pagina()

    # --- primitivas -------------------------------------------------------------------------------------------

    def _nova_pagina(self) -> None:
        self.paginas.append([])
        self.y = self.alt - self.topo

    def _op(self, dados: bytes) -> None:
        self.paginas[-1].append(dados)

    def _fonte(self, negrito: bool) -> bytes:
        return b"/F2" if negrito else b"/F1"

    def texto_em(self, x: float, y: float, s: str, tam: float = 10, negrito: bool = False, cinza: float = 0) -> None:
        self._op(
            b"BT %b %.2f Tf %.2f g %.2f %.2f Td (" % (self._fonte(negrito), tam, cinza, x, y) + _pdf_str(s) + b") Tj ET"
        )

    def linha(self, x1: float, y1: float, x2: float, y2: float, espessura: float = 0.5, cinza: float = 0.6) -> None:
        self._op(b"%.2f G %.2f w %.2f %.2f m %.2f %.2f l S" % (cinza, espessura, x1, y1, x2, y2))

    def retangulo(self, x: float, y: float, w: float, h: float, cinza: float = 0.93) -> None:
        self._op(b"%.2f g %.2f %.2f %.2f %.2f re f" % (cinza, x, y, w, h))

    # --- fluxo ------------------------------------------------------------------------------------------------

    @property
    def largura_util(self) -> float:
        return self.larg - 2 * self.m

    def garante(self, altura: float) -> None:
        if self.y - altura < self.base:
            self._nova_pagina()

    def espaco(self, n: float) -> None:
        self.y -= n

    def paragrafo(
        self,
        texto: str,
        tam: float = 10,
        negrito: bool = False,
        cinza: float = 0,
        entre: float = 3,
        centro: bool = False,
    ) -> None:
        for ln in quebra(texto, self.largura_util, tam, negrito):
            self.garante(tam + entre)
            self.y -= tam
            x = self.m + ((self.largura_util - largura(ln, tam, negrito)) / 2 if centro else 0)
            self.texto_em(x, self.y, ln, tam, negrito, cinza)
            self.y -= entre

    def regua(self, espaco_antes: float = 4, espaco_depois: float = 6) -> None:
        self.garante(espaco_antes + espaco_depois + 1)
        self.y -= espaco_antes
        self.linha(self.m, self.y, self.larg - self.m, self.y)
        self.y -= espaco_depois

    def pares(self, itens: list[tuple[str, str]], tam: float = 10) -> None:
        """Linhas 'Rótulo: valor' com o rótulo em negrito."""
        for rot, val in itens:
            self.garante(tam + 4)
            self.y -= tam
            self.texto_em(self.m, self.y, rot, tam, True)
            self.texto_em(self.m + largura(rot, tam, True) + 4, self.y, val, tam)
            self.y -= 4

    def tabela(self, colunas: list[tuple[str, float, str]], linhas: list[list[str]], tam: float = 9) -> None:
        """colunas: (título, largura em pontos, alinhamento 'e'|'d'|'c'). Repete o cabeçalho ao mudar de página."""
        pad, alt_ln = 4.0, tam + 7

        def cabecalho() -> None:
            self.garante(alt_ln * 2)
            self.retangulo(self.m, self.y - alt_ln, sum(c[1] for c in colunas), alt_ln, 0.9)
            x = self.m
            for tit, w, al in colunas:
                self._celula(x, self.y - alt_ln + 4, w, tit, tam, True, al, pad)
                x += w
            self.y -= alt_ln

        cabecalho()
        for ln in linhas:
            celulas = [quebra(c, w - 2 * pad, tam) for c, (_, w, _) in zip(ln, colunas, strict=True)]
            n = max(len(c) for c in celulas)
            altura = n * (tam + 2) + 5
            if self.y - altura < self.base:
                self._nova_pagina()
                cabecalho()
            x = self.m
            for linhas_c, (_, w, al) in zip(celulas, colunas, strict=True):
                for i, txt in enumerate(linhas_c):
                    self._celula(x, self.y - (i + 1) * (tam + 2) - 1, w, txt, tam, False, al, pad)
                x += w
            self.y -= altura
            self.linha(self.m, self.y, self.m + sum(c[1] for c in colunas), self.y, 0.3, 0.8)

    def _celula(self, x: float, y: float, w: float, s: str, tam: float, negrito: bool, al: str, pad: float) -> None:
        wt = largura(s, tam, negrito)
        px = x + pad if al == "e" else (x + w - pad - wt if al == "d" else x + (w - wt) / 2)
        self.texto_em(px, y, s, tam, negrito)

    # --- saída ------------------------------------------------------------------------------------------------

    def bytes(self, quando: datetime | None = None) -> bytes:
        total = len(self.paginas)
        for i, pg in enumerate(self.paginas, 1):  # rodapé em todas as páginas
            self.paginas[i - 1] = pg
            self._rodape(i, total, pg)
        quando = quando or datetime.now(UTC)
        objs: list[bytes] = [b""] * (4 + 2 * total)
        objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
        kids = b" ".join(b"%d 0 R" % (5 + 2 * i) for i in range(total))
        objs[1] = b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % total
        objs[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
        for i, pg in enumerate(self.paginas):
            fluxo = b"\n".join(pg)
            objs[4 + 2 * i] = (
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.0f %.0f] /Contents %d 0 R "
                b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >>" % (self.larg, self.alt, 6 + 2 * i)
            )
            objs[5 + 2 * i] = b"<< /Length %d >>\nstream\n" % len(fluxo) + fluxo + b"\nendstream"
        info = (
            b"<< /Title "
            + _hex_utf16(self.titulo)
            + b" /Producer (Caderneta) /CreationDate (D:%b) >>" % quando.strftime("%Y%m%d%H%M%SZ").encode()
        )
        objs.append(info)
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offs = []
        for n, o in enumerate(objs, 1):
            offs.append(len(out))
            out += b"%d 0 obj\n" % n + o + b"\nendobj\n"
        xref = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
        out += b"".join(b"%010d 00000 n \n" % o for o in offs)
        out += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objs) + 1,
            len(objs),
            xref,
        )
        return bytes(out)

    def _rodape(self, i: int, total: int, pg: list[bytes]) -> None:
        y = self.base - 24
        pg.append(b"0.6 G 0.5 w %.2f %.2f m %.2f %.2f l S" % (self.m, y + 12, self.larg - self.m, y + 12))
        if self.rodape:
            pg.append(b"BT /F1 8 Tf 0.35 g %.2f %.2f Td (" % (self.m, y) + _pdf_str(self.rodape) + b") Tj ET")
        marca = f"Página {i} de {total}"
        pg.append(
            b"BT /F1 8 Tf 0.35 g %.2f %.2f Td (" % (self.larg - self.m - largura(marca, 8), y)
            + _pdf_str(marca)
            + b") Tj ET"
        )
