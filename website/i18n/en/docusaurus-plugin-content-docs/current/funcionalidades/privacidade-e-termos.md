---
title: Privacy and terms
---

# Privacy policy and terms of use

Caderneta has a **privacy policy** and **terms of use** in plain language, public (readable before signing in) and with **confirmation recorded per version**.

:::note The texts themselves are in Portuguese
The texts shown in the app (`/privacidade` and `/termos`) are in **Portuguese (Brazil)**, because they apply Brazilian law and are meant to be reviewed by Brazilian lawyers. Each installation can replace them with its own lawyer-approved versions.
:::

## How it works

- **Where to read:** `/privacidade` and `/termos`, without login, and in the footer links of the app and of the sign-in screen.
- **First access:** before using the app, the person reads and ticks **"I have read and I am aware"**. This is **acknowledgement** of the text, not consent to data processing: the legal basis is the school's contract (see the policy).
- **New text:** when the version changes, everyone sees the confirmation screen again at the next access. The confirmation stores **who**, **which text**, **which version** and **when**, and goes in the audit log.
- **Offline** (teacher offline mode), the confirmation waits until the next online access.
- **Data protection officer (DPO):** the principal's office enters the name and e-mail under **School**. The contact appears in the policy (for signed-in users) and in **My data**.
- **Cookies:** there is only the session cookie, which is essential. That is why **there is no cookie notice**, and the policy explains this, together with the encrypted offline-mode storage.

## Who is the operator in this installation

Caderneta is free software: the name belongs to the program, not to a company. That is why the texts say "the operator of this installation" and **each installation sets its own** in the server configuration:

- `CADERNETA_OPERADORA_NOME`: who hosts and maintains this installation (company, person or the school itself).
- `CADERNETA_OPERADORA_CONTATO`: contact e-mail or phone (optional).

Without it, the text shows an uppercase reminder to fill in. If the school itself hosts, it is controller and operator at the same time, and the policy says so.

## For whoever maintains the texts

The texts live in `api/app/legal/privacidade.md` and `termos.md`, with `versao` (version), `titulo` (title) and `status` at the top.

- Changed something relevant? **Change the `versao`.** The `test_legal.py` test checks that the policy cites the periods and features the system really has (365 and 180 days, My data, 15 days, 5 years, cookie, offline, DPO), so the text does not fall behind.
- `status: rascunho` (draft) shows the **"Version under legal review"** banner. After the opinion, switch to `vigente` (in force) and update the version.
- Passages in brackets and uppercase (`[... TO BE CONFIRMED IN THE LEGAL OPINION]`) are points that depend on the lawyer or on deployment.
- **Own texts per installation:** point `CADERNETA_LEGAL_DIR` to a folder with `privacidade.md` and/or `termos.md` in the same format; whatever is missing falls back to the project's default text.

## What still depends on the opinion

See `.lgpd/gaps.md` (T30 and T31): legal basis for health data, acknowledgement by guardians for minors' student accounts, list of providers and international transfer, audit and backup periods, jurisdiction and liability in the terms.

:::note Not legal advice
This is a **technical draft** written from the data map and the laws. It should only be published to schools **after review by a lawyer** specialized in data protection.
:::
