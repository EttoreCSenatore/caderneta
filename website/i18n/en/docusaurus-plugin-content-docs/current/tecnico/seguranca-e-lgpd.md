---
title: Security and LGPD
---

# Security and LGPD

Caderneta holds data about **children and teenagers**, including **health data**. Under the LGPD (the Brazilian data protection law) this means:
data about minors must be processed in their **best interest** (art. 14) and health data is **sensitive** (art. 11).
Security is a requirement from the first milestone, not a final step.

:::info Compliance status
[M8 of the roadmap](../roadmap.md) brings together the general review of security, licenses and LGPD compliance. The code and documentation work is done:
[security review](./revisao-de-seguranca.md), [data subject rights](../funcionalidades/direitos-do-titular.md), [privacy and terms](../funcionalidades/privacidade-e-termos.md),
[ROPA, RIPD and incident plan](./documentos-de-conformidade.md), [backups, keys and logs](./backups-chaves-e-logs.md) and the [lawyer package](./pacote-juridico.md).
**The legal opinion and the third-party penetration test are still missing**, and both are external. The data map and the gaps are in
[`.lgpd/`](https://github.com/EttoreCSenatore/caderneta/tree/main/.lgpd).
:::

## Roles under the LGPD

- **Controller**: the school, which decides why and how the data is used.
- **Operator**: whoever hosts and maintains the installation (it can be the school itself), following the school's instructions (data processing agreement).
- **Data subjects**: students, guardians and staff.

## What is implemented

- **Access:** Argon2id, progressive lockout, 2FA mandatory for the principal's office and coordination with single-use codes, single-use invitations, per-IP attempt limits, password change and "sign out of all devices".
- **Sessions and web:** server-side sessions (only the token hash), `HttpOnly` + `SameSite=Lax` + `Secure` cookie, CSRF protection by header, security headers (CSP, HSTS, `nosniff`...), the service worker never stores API responses.
- **Isolation:** per-school Row-Level Security with an unprivileged database role; isolation tests and a test that walks every route and requires login outside the public list.
- **Sensitive data:** health file and 2FA secrets encrypted with AES-256-GCM (per-record associated data), with **key rotation**; teachers see only the summary alert; full reads are audited.
- **Files:** encrypted at rest, antivirus on upload (fail closed), images without EXIF, download through a 5-minute signed link ([ADR 0004](../decisoes/armazenamento-de-arquivos.md)).
- **Minimal communication:** e-mail and push **without content**, adults only; quiet hours.
- **Traceability:** insert-only audit log; logs without personal data (no query string or URL secrets).
- **Retention:** notifications, attachments, drafts, removed notes, push devices and **leavers** have periods and automatic deletion, with notice beforehand.
- **Data subject rights:** download your own data instantly, requests with a 15-day deadline and a queue for the principal's office.
- **Transparency:** public privacy policy and terms, acknowledgement recorded per version, DPO shown in the app.
- **Backups:** encrypted, with a restore test that checks the keys.
- **Teacher offline mode:** encrypted vault on the device, erased on sign-out and after 7 days without a connection.

Login details in [Access, invitations and 2FA](../funcionalidades/acesso-e-convites.md).

## Measures by topic

### Access

- Authentication with a strong password, attempt limits and progressive lockout.
- **2FA (TOTP) mandatory** for administrators and coordination; optional for the rest (maintainer's decision, to be revisited in the legal opinion).
- Invitations through a single-use link that expires; no open sign-up.
- **Authorization in two layers**: the API checks the role and the link; PostgreSQL applies Row-Level Security per school,
  so an API mistake does not leak another school's data.

### Data

- TLS on all traffic; HSTS and a restrictive CSP.
- Health file **encrypted at field level**, with the key kept outside the database.
- **Minimization**: CPF and documents are optional; teachers see summary health alerts, not medical reports.
- Encrypted daily backups, copy off the server, monthly restore test (scripts in `infra/backup/`).
- Hosting preferably in **Brazil** (to be chosen).

### Traceability

- Insert-only audit log for: grade changes after closing, reads of the health file and of reserved notes, file downloads, data exports, answers to data subject requests.

### Data subject rights

- A guardian sees and downloads their child's data; correction, deletion and portability requests through the app, with a deadline.
- Retention: data of those who left is deleted after the period the school sets, with notice beforehand; the school history is kept ([Leavers](../funcionalidades/desligados.md)).

### Development

- Dependencies audited in CI (`pip-audit`, `npm audit`), license audit, SBOM and production-image build. Dependabot with a 7-day wait; Actions pinned to a commit and images by digest.
- Automated permission tests: for each role, what it **cannot** see.
- Fictitious data in every non-production environment; never copy production to dev.
