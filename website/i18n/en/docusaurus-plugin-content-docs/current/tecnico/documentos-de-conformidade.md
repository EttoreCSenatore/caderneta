---
title: Compliance documents (M8.4)
---

# Compliance documents: ROPA, RIPD and incidents

These documents live in the repository, in [`.lgpd/`](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd), versioned together with the code. They are **technical drafts** made with the methodology of the `lgpd-audit` skill and **depend on review by the DPO and a lawyer**; they are not a legal opinion. The documents themselves are **in Portuguese** (Brazilian law, Brazilian reviewers); this page describes them.

| Document | What it is for | Where |
|---|---|---|
| **Data map** | What data, why, legal basis, for how long (A001 to A019) | [data-map.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/data-map.md) |
| **ROPA** (art. 37) | Record of processing operations, as controller (the school) and operator | [ROPA.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/ROPA.md) |
| **RIPD** (art. 38, data protection impact assessment) | Risks to data subjects and measures, with a probability and impact matrix and a preliminary ECA Digital assessment | [RIPD.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/RIPD.md) |
| **Legitimate-interest tests (LIA)** | Why legitimate interest holds for 5 operations and with which safeguards | [lia/](https://github.com/EttoreCSenatore/caderneta/tree/main/.lgpd/lia) |
| **Incident response plan** (art. 48) | What to do in the first hours, deadlines, who decides and communication templates | [runbook.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/incidentes/runbook.md) |
| **Incident log** | Template of the 5-year record, mandatory even without a notification | [log.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/incidentes/log.md) |
| **Gaps** | Prioritized pending items (legal and technical) | [gaps.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/gaps.md) |

## How each installation uses them

- Caderneta is free software: **each school and each operator completes** the names (legal name, CNPJ, DPO, on-call person) and keeps its own ROPA, RIPD and incident log.
- Every new feature that handles personal data updates the data map, the ROPA and, if the risk changes, the RIPD, in the same PR.

## What the incident plan already brings

- **Containment tool:** `python -m app.cli revogar-sessoes [escola_id]` ends all sessions of the installation or of one school.
- **For one person:** *My account → Sign out of all devices* (also cancels push).
- **Step by step:** open and note the moment of awareness, contain and preserve evidence, size it up (separating children and teenagers), decide with legal whether it is notifiable, notify the ANPD and the data subjects within 3 business days, record it.
- **Note:** since almost all data on the platform belongs to children or teenagers, an incident with real exposure tends to be notifiable. The DPO decides together with legal.

## What is still missing

The legitimate-interest tests are in draft and wait for the legal opinion. See `T32` to `T34` in [gaps.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/gaps.md): on-call names and phones (the school's on-call person is the school's IT person) and an incident **drill**; the operation contract with each school and return of the data at its end.

:::note Check against the official text
The ANPD resolutions (2/2022, 15/2024 and others) are not yet in the `ctresb/leis` repository. Deadlines and items come from the skill's description and **must be checked against the official text** in the legal review.
:::
