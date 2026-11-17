---
title: Pilot plan
---

# Pilot plan (M9)

The pilot is the first use **with real data**, at one school, at a small scale and with close follow-up. This plan applies to any new installation; adjust names and dates.

## 1. Entry gate: it only starts with all of this ticked (go / no-go)

**Legal and privacy** (see the [lawyer package](./tecnico/pacote-juridico.md))
- [ ] Package generated, reviewed by the school's and/or operator's lawyer, and a **signed legal opinion**
- [ ] Privacy and terms texts **approved** (`status: vigente`) and published
- [ ] **Operation contract** signed (if the operator is not the school)
- [ ] **DPO** appointed and shown in the app; operator configured
- [ ] Guardians informed about the use of the platform and, for **children**, acknowledgement/consent per the opinion

**Security and operations** (see [Deployment](./tecnico/implantacao.md) and [Backups, keys and logs](./tecnico/backups-chaves-e-logs.md))
- [ ] Installation online with **HTTPS**, `smoke.sh` with no failures
- [ ] **Penetration test** done, with no critical or high finding left
- [ ] **Encrypted backup** running and **restore test** done successfully; data key and backup password kept off the server
- [ ] **Monitoring and alerts** active (`verificar.sh`) with alerts to the on-call person
- [ ] **On-call person** defined (the school's IT person and the operator's, with phone) and an **incident drill** done
- [ ] Test on **real devices**: Android and iPhone, app installed, **opening without internet**, entering a grade and roll call offline, **push** (needs HTTPS and VAPID keys)

**People**
- [ ] Principal's office and teachers **trained**; support guide delivered
- [ ] Support channel agreed (who, where, how fast)

## 2. Phases

| Phase | Who uses it | Suggested duration | What happens |
|---|---|---|---|
| 0. Preparation | Technical team and principal's office | 1 to 2 weeks | Install, import students and classes (first in the demo), register staff, train |
| 1. Staff | Principal's office, coordination and teachers | 2 weeks | Enter **grades and roll call**, use the calendar and exams. **Families not yet**. Confirm that daily work runs |
| 2. Families of 1 or 2 classes | + guardians of those classes | 2 to 4 weeks | Invitations, notices, authorizations, messages, report card. Follow questions and data subject requests |
| 3. Whole school | All classes | until the end of the term | Expand with the routine already stable |
| 4. Closing | Everyone | 1 week | Review, decision (continue, adjust or stop) and report |

Move to the next phase only with the previous one **free of serious issues** and the on-call person with no open incident.

## 3. Data import

1. First import a **fictitious copy** (same format) to rehearse.
2. Use the **Import** screen (CSV): check duplicate students, classes and guardians.
3. Register only what is needed: the **student's CPF is optional**; the health file only what the school needs.
4. Keep the original file only as long as needed and **delete it** from the computer after importing.

## 4. Support and severity

| Severity | Example | First response |
|---|---|---|
| **Critical** | A student's data showing up for someone who should not see it; site down during class hours; suspected break-in | **Immediate**: call the on-call person and follow the [incident plan](./tecnico/documentos-de-conformidade.md) |
| High | Cannot enter a grade or roll call; e-mails not going out | same day |
| Medium | Calculation error, broken screen on one device | within 2 business days |
| Low | Suggestion, wording, improvement | at the weekly review |

Log each ticket without student personal data (describe the problem, **do not** paste a name, grade or message).

## 5. How to tell it worked (without collecting personal data)

- Teachers who **entered grades and roll call** on the platform instead of paper (a count).
- **Roll calls and grades** entered offline and sent without loss.
- Families **invited** and who **signed in**.
- **Data subject requests** received and **answered on time** (goal: 100% within 15 days).
- **Security incidents**: goal zero; any one is recorded and handled.
- Tickets by severity and **response time**.
- A short anonymous satisfaction survey with teachers and families.

## 6. Rollback plan

If something serious happens: **go back to the previous process (paper)** while it is fixed. To stop access: `python -m app.cli revogar-sessoes` and stop the `web` service. The data is preserved; the school decides, with the DPO, what to communicate. **Take a backup before any update.**

## 7. Closing the pilot

- A **report** with the metrics above, what worked, what did not, incidents and data subject requests.
- The school's **decision**: continue, adjust or stop.
- If stopping: **export** whatever the school wants and **delete** the rest (including backups in their cycle), per the contract; confirm in writing.
- **Review** the lawyer package and the RIPD with what was learned.
