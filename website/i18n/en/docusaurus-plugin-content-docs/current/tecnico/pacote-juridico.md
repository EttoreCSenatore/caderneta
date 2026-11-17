---
title: Lawyer package
---

# Legal review package (one per installation)

Caderneta is free software: **each school, or whoever serves it, installs its own**, and each case has its own legal reality (size, providers, country, contract). That is why the project ships a **lawyer-package generator**: a single document, assembled with that installation's data, which the school or the operator hands to **their own lawyer** for review.

## What the package contains

| Part | What it is |
|---|---|
| **1. Cover letter** | What the project is, the roles, what is asked of the lawyer and what the package is **not** |
| **2. Installation sheet** | School, DPO, operator, on-call person, providers and countries, configured periods, where the keys are kept |
| **3. Questions** | 14 objective questions, each with **what the system does today**, the **default recommendation** and the **decision requested**, with room to answer |
| **4. Operation contract** | Minimum points (art. 39) for the lawyer to draft |
| **5. Opinion and checklist** | Template to record the outcome and the installer's step by step after the opinion |
| **Annexes A to H** | Data map, privacy policy and terms **of this installation**, ROPA, RIPD, legitimate-interest tests, incident plan, gaps |

The package is generated **in Portuguese**, for Brazilian lawyers.

## How to generate

1. Copy the template and fill in the installation's data:

   ```bash
   cp .lgpd/pacote/instalacao.exemplo.json instalacao.json
   ```

2. Generate the package:

   ```bash
   python3 scripts/gerar-pacote-juridico.py --instalacao instalacao.json --saida pacote-juridico
   ```

3. Open `pacote-juridico/pacote-juridico.html` in the browser and **print to PDF** (or send the `.md`). Fields without data show in red as **[A PREENCHER: field]** ("to fill in") and the command lists what is missing.

`instalacao.json` and the generated folder stay out of Git (they hold the school's data).

## Own legal texts for each installation

The lawyer can **rewrite** the privacy policy and the terms. The installation then uses their version like this:

1. Create a folder with `privacidade.md` and/or `termos.md`, in the same format as those in `api/app/legal/` (a header with `versao`, `titulo` and `status`; use `status: vigente` and a new `versao`).
2. Point `CADERNETA_LEGAL_DIR` to that folder (and, for the generator, the `textos_legais_dir` field of `instalacao.json`).
3. Whatever is missing from the folder uses the project's default text. Everyone confirms the acknowledgement of the new version at their next access.

The operator appears in the texts through the variables `CADERNETA_OPERADORA_NOME` and `CADERNETA_OPERADORA_CONTATO`.

## When to redo it

Resend the package to the lawyer **when a new feature with personal data comes in**, **when the provider** or country **changes**, **when the operator changes** and **every 12 months**. The package is always built from the current version of the project and the data map, so it does not go stale.

:::note Not legal advice
The package was prepared by the developers with the public methodology of `lgpd-skills` and the texts of `leis`. **It does not replace the legal opinion.** The ANPD resolutions it cites must be checked against the official text.
:::
