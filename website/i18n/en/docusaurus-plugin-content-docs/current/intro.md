---
id: intro
title: Overview
slug: /intro
---

# Caderneta

**Caderneta** is a lightweight web platform for schools. It brings together, in one place, what is today scattered across
paper gradebooks, spreadsheets, WhatsApp groups and bulletin boards:

- **Grades and averages**: the teacher enters grades and the average is calculated automatically, using the school's rule.
- **Live report card**: students and guardians follow grades, averages and absences at any time.
- **Communication**: notices for everyone, for a class or for one student, and messages to the family with read confirmation.
- **Calendar**: the school sets holidays, events and days off; each teacher adds events only for their own classes.
- **Exams and assignments**: the teacher uploads the file and the school receives it in an organized print queue.
- **Student file and history**: personal data, family contacts, health information and notes that
  follow the student from one year to the next.

:::info Status
**M1 to M7 are done**: login with 2FA and invitations, classes and students, grades and averages, attendance, communication (notices, messages, authorizations, notifications and push), calendar, exams and printing, history and notes, school-history PDF, teacher offline mode and an installable PWA. **M8** (compliance and security): the code and documentation work is done; the lawyer's opinion and the penetration test are still pending. **M9** (pilot): being prepared. See the [roadmap](./roadmap.md).
:::

![Principal's dashboard](/img/screenshots/admin-inicio.png)

## Who uses it

| Role | What they do in Caderneta |
|---|---|
| **School** (principal's office and secretariat) | Sets up classes, students and teachers, defines the calendar, publishes school-wide notices, prints exams |
| **Coordination** | Follows grades and attendance, approves exams, records pedagogical notes |
| **Teacher** | Enters grades and absences, uploads exams and assignments, notifies their classes, creates class events |
| **Guardian** | Sees each child's grades, averages, absences, notices and messages; confirms reading |
| **Student** | Sees their own grades, averages, absences, calendar and class notices |

Details in [Roles and permissions](./produto/perfis.md).

## Principles

1. **Easy before complete.** Each screen solves one task. Entering a class's grades should take less time than in the spreadsheet.
2. **Lightweight.** Works on basic phones and 3G. No heavy app to download: it is a website that can be installed on the home screen.
3. **Private by default.** The data belongs to children and teenagers, some of it health data. Each person sees only what they need to see
   ([Security and LGPD](./tecnico/seguranca-e-lgpd.md)).
4. **Built for the Brazilian school.** Two-month or three-month terms, recovery exams, 75% minimum attendance, national and local holidays.

## How this documentation is organized

- **Product**: [vision](./produto/visao.md), [roles](./produto/perfis.md) and [journeys](./produto/jornadas.md) of each user.
- **Features**: one page per area, with rules, screens and acceptance criteria.
- **Technical**: [architecture](./tecnico/arquitetura.md), [data model](./tecnico/modelo-de-dados.md),
  [security and LGPD](./tecnico/seguranca-e-lgpd.md) and [how to run locally](./tecnico/desenvolvimento.md).
- **Decisions (ADRs)**: the reasons behind the technical choices.
- **[Roadmap](./roadmap.md)**: the delivery milestones.

:::note About languages
This site is available in Portuguese (Brazil) and English. The legal and compliance artifacts (privacy policy and terms of use shown in the app, ROPA, RIPD, legitimate-interest tests, incident plan and the lawyer package) are **in Portuguese**, because they apply Brazilian law (LGPD, ECA Digital) and are reviewed by Brazilian lawyers. The pages here describe them in English.
:::
