---
title: Leavers
---

# Students and users who have left

Personal data that has lost its purpose must be deleted (LGPD, arts. 15 and 16). At the same time, the school must **keep the history** of those who passed through it.
The **Leavers** section (principal's office and coordination see it; only the principal's office acts) separates the two: it keeps the historical core and **deletes the rest after a period, with notice beforehand**.

## Who is included

- **Student who left:** status transferred, completed or archived. The count starts at the moment the status stops being "active"
  (including at re-enrollment). Going back to "active" **cancels** the count, the postponement and the notice.
- **User who left:** profile deactivated under Staff (employee), or a guardian or student account left without any link after the student's data was deleted.

## What stays and what goes

| | Stays (history) | Goes after the period |
|---|---|---|
| **Student** | name, birth date, RA, enrollments, **grades**, **attendance** (status only) and the **histories issued** | health file, **notes and all versions**, conversations, messages and attachments (files deleted from disk), guardian contacts, authorization answers, CPF and **absence justifications** (free text, which can reveal health) |
| **User** | what they wrote remains, attributed to **"Former user"** | name, e-mail, phone, password, 2FA, sessions, push devices, tokens and invitations. The account is **anonymized** |

The school-history PDF keeps coming out normally after the deletion, because it uses only the retained core.

## Periods and notice

- **Periods configurable by the principal's office** (default: **365 days** for student data, **180 days** for accounts, **notice 30 days before**). The minimum accepted is 30 days,
  and the notice must be shorter than the periods. Confirm with the legal team the minimum retention period for the school history in your school's education network.
- **Notice before deleting:** on entering the notice window, the principal's office receives a notification ("Leavers' data will be deleted soon") and the people affected receive
  an **e-mail without content**: the student's guardian and the user who left. That leaves time to ask for a copy of the data. Guardians with a **restricted** link are not notified.
- **Guarantee:** deletion **only happens after the notice was given with the configured lead time**. If the period expires before the notice, the deletion waits.
- **Postpone** (principal's office): 30, 90, 180 days or 1 year from today. Postponing **restarts the notice**. Each postponement goes in the audit log.
- **Delete now** (student, principal's office): to answer a data subject's request. Requires typing `APAGAR` ("delete"), is irreversible and goes in the audit log, with counts only, no personal data.

## Details

- An account is **only anonymized when all of its profiles are left and expired**. Someone who still has active access at another school keeps the account, and only the link to
  this school becomes inactive.
- The audit log records `desligados.purgar_aluno`, `desligados.anonimizar_usuario`, `desligados.adiar_*` and `desligados.config`, **without names or content**.
- The work runs in the worker (`python -m app.cli notificar`), together with the other retention routines.

![Students who left](/img/screenshots/desligados-alunos.png)

![Users who left](/img/screenshots/desligados-usuarios.png)

![Periods](/img/screenshots/desligados-prazos.png)

## Acceptance criteria

- [x] Separate leavers area with a countdown
- [x] Notice before deleting (principal's office and affected people) and a postpone option
- [x] Historical core kept and complementary data deleted
- [x] Accounts anonymized, keeping authorship as "Former user"
- [ ] Minimum retention period for the school history confirmed by the legal team (M8)
