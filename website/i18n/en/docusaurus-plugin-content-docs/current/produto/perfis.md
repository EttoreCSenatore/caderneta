---
title: Roles and permissions
---

# Roles and permissions

Each person signs in with their own account and one or more **roles** inside a school. A teacher can also be
a guardian of a student at the same school; in that case, they switch between roles in the menu.

## Roles

| Role | Who | Scope |
|---|---|---|
| **School administrator** | Principal's office, secretariat | The whole school |
| **Coordination** | Pedagogical coordinator | The segments or classes they coordinate |
| **Teacher** | Teaching staff | The classes and subjects assigned to them in the school year |
| **Guardian** | Father, mother, legal guardian | The students they are linked to |
| **Student** | Pupil (from an age defined by the school) | Themselves |

## Permission matrix

Legend: ✏️ creates and edits · 👁️ view only · — no access

| Resource | School | Coordination | Teacher | Guardian | Student |
|---|---|---|---|---|---|
| Classes, subjects, school year | ✏️ | 👁️ | 👁️ (their own) | — | — |
| Student file (data and contacts) | ✏️ | 👁️ | 👁️ (their students) | ✏️ (contacts) | 👁️ |
| Health information | ✏️ | 👁️ | 👁️ essential alerts | ✏️ | — |
| Grades and assessments | 👁️ (can correct with a justification) | 👁️ | ✏️ (their classes) | 👁️ | 👁️ |
| Average calculation rule | ✏️ | 👁️ | 👁️ | — | — |
| Attendance | 👁️ | 👁️ | ✏️ (their classes) | 👁️ | 👁️ |
| School-wide notices | ✏️ | ✏️ | 👁️ | 👁️ | 👁️ |
| Class notices | ✏️ | ✏️ | ✏️ (their classes) | 👁️ | 👁️ |
| Message to a student/family | ✏️ | ✏️ | ✏️ (their students) | 👁️ and replies | — |
| School calendar | ✏️ | 👁️ | 👁️ | 👁️ | 👁️ |
| Class events | ✏️ | ✏️ | ✏️ (their classes) | 👁️ | 👁️ |
| Exams and assignments (files) | 👁️ and prints | 👁️ and approves | ✏️ | — | — |
| Notes about the student | ✏️ | ✏️ | ✏️ (their students) | 👁️ only those marked visible | — |
| Audit log | 👁️ | — | — | — | — |

:::tip Golden rule
The server decides what each person sees. The interface only hides buttons; access is guaranteed by the database, with
rules per school and per link (see [Security and LGPD](../tecnico/seguranca-e-lgpd.md)).
:::

## Each role has its own home screen

The family sees their children; the student sees their own data. Since M2 this screen shows grades, absences and notices.

<div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
  <img src="/caderneta/img/screenshots/familia-inicio-celular.png" alt="Guardian home on the phone" width="280" />
  <img src="/caderneta/img/screenshots/aluno-inicio-celular-escuro.png" alt="Student home on the phone, dark theme" width="280" />
</div>

The principal's and the teacher's screens are in [School, classes and staff](../funcionalidades/escola-e-turmas.md).

## Student accounts

- The school decides from which grade a student has their own login (suggestion: 6th grade).
- Younger students join by invitation from the guardian or the school; there is no open sign-up.
- For the early grades, follow-up is done only through the guardian's account.

## Guardian links

- A student can have several guardians; a guardian can have several children (even at different schools in the future).
- Each link has a type (mother, father, guardian, other) and flags: **may pick up the student**, **receives notices**,
  **is the emergency contact**.
- The school can restrict a guardian (e.g., a court order) without erasing the history.
