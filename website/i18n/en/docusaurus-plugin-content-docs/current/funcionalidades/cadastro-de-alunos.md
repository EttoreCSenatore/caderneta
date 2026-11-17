---
title: Student registration
---

# Student registration

The student file is the basis of everything. It is created by the school (manually or by spreadsheet) and completed by the guardians.

:::tip Delivered in M1
Registration, guardians, health file and spreadsheet import already work.
:::

![Student list with search and filter by class](/img/screenshots/alunos.png)

![Student file: data](/img/screenshots/aluno-dados.png)

## File data

| Group | Fields | Who edits |
|---|---|---|
| **Identification** | First name, surname, social name, date of birth, photo (optional), enrollment/RA number | School |
| **Documents** | CPF (optional), birth certificate (optional) | School |
| **Family** | Linked guardians, type of link, phones, e-mail, who may pick up | School and guardian |
| **Emergency** | Emergency contact, health plan (optional) | School and guardian |
| **Health** | Allergies, continuous-use medication, conditions (e.g., asthma, diabetes), dietary restrictions, medical reports and specific educational needs | School and guardian |
| **School** | Current class, status (active, transferred, completed), class history | School |

## Guardians

Under the **Family** tab, the school registers the guardians with the type of link and each one's permissions (pick up the student,
receive notices, emergency contact, restricted access). Badges show who already uses the app and who has a pending invitation.
The guardian can update their own phone and e-mail.

![Student's guardians](/img/screenshots/aluno-familia.png)

## Health information

This is **sensitive data** under the LGPD. Therefore:

- it lives in a separate, encrypted table, and every read is recorded in the audit log;
- teachers see only a **summary alert** ("Severe peanut allergy: carries adrenaline in the backpack") defined by the school,
  not the full medical report;
- the guardian is the one who provides and updates it, and the school confirms.

![Health file seen by the school](/img/screenshots/aluno-saude.png)

On the phone, the guardian sees and updates their child's file:

<img src="/caderneta/img/screenshots/familia-saude-celular.png" alt="Health file on the guardian's phone" width="320" />

## Spreadsheet import

- A CSV template to download, with student, guardian and class columns.
- Preview before saving: shows rows with errors (invalid date, repeated e-mail) without importing anything halfway.
- After importing, the school sends the invitations to the guardians.
- Accepts Brazilian Excel files (`;` separator, Windows-1252 encoding) and `dd/mm/yyyy` dates.
- **All or nothing**: if any row has an error, nothing is saved.

![Preview with per-row errors](/img/screenshots/importar-erros.png)

## Acceptance criteria (M1) ✅

- [x] The school creates, edits and archives students (without erasing history)
- [x] CSV import with preview and error report
- [x] Several guardians linked, with pick-up, notices and emergency flags
- [x] Single-use invitation link that expires in 7 days
- [x] Health information encrypted and with audited reads
