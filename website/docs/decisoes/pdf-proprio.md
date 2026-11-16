---
title: "ADR 0005: gerador de PDF próprio"
sidebar_label: "ADR 0005: PDF próprio"
---

# ADR 0005: gerador de PDF próprio, sem biblioteca

- **Status:** aceita (2026-11-16)
- **Contexto:** o histórico escolar precisa sair em PDF (texto, tabelas, várias páginas). As bibliotecas comuns (ReportLab, WeasyPrint,
  fpdf2) trazem dependências, licenças diferentes (algumas com cláusulas fortes) e superfície de ataque, e cada uma entra na
  auditoria de licenças e de segurança do M8.

## Decisão

Um gerador mínimo em `app/pdfmin.py` (cerca de 200 linhas, só biblioteca padrão):

- páginas A4, **Helvetica e Helvetica-Bold** (fontes padrão de todo leitor de PDF, sem incorporar arquivos de fonte);
- codificação **WinAnsi (cp1252)**, que cobre o português; caracteres fora dela viram `?`;
- métricas AFM da Helvetica para **medir e quebrar linhas**, tabelas com cabeçalho repetido ao virar a página, rodapé com "Página X de Y";
- tabela de referências cruzadas e `startxref` corretos (testados).

## Consequências

- Zero dependência nova e nenhuma licença a mais. O código é nosso e pequeno o bastante para revisar.
- Só serve a documentos simples (texto e tabelas). Gráficos, imagens, fontes próprias e idiomas fora do alfabeto latino exigem
  trocar por uma biblioteca, e esta ADR deve ser revista nesse caso.
- Os testes conferem a estrutura do PDF e o texto; a aparência foi conferida abrindo o arquivo em um leitor.
