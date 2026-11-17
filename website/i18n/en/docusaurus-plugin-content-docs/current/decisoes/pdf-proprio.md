---
title: "ADR 0005: in-house PDF generator"
sidebar_label: "ADR 0005: own PDF"
---

# ADR 0005: in-house PDF generator, no library

- **Status:** accepted (2026-11-16)
- **Context:** the school history must come out as a PDF (text, tables, several pages). Common libraries (ReportLab, WeasyPrint,
  fpdf2) bring dependencies, different licenses (some with strong clauses) and attack surface, and each one enters the
  license and security audit of M8.

## Decision

A minimal generator in `app/pdfmin.py` (about 200 lines, standard library only):

- A4 pages, **Helvetica and Helvetica-Bold** (standard fonts in every PDF reader, without embedding font files);
- **WinAnsi (cp1252)** encoding, which covers Portuguese; characters outside it become `?`;
- Helvetica AFM metrics to **measure and wrap lines**, tables with a header repeated when the page turns, footer with "Page X of Y";
- a correct cross-reference table and `startxref` (tested).

## Consequences

- Zero new dependencies and no extra license. The code is ours and small enough to review.
- It only serves simple documents (text and tables). Charts, images, custom fonts and languages outside the Latin alphabet require
  switching to a library, and this ADR must be revisited in that case.
- The tests check the structure of the PDF and the text; the appearance was checked by opening the file in a reader.
