---
title: History and notes
---

# Student history and notes

What is known about the student must not be lost when the year or the teacher changes.

## History

- Each **enrollment** links the student to a class in a school year. Grades, attendance and notes are tied to the enrollment,
  so the history of previous years stays intact.
- **Bulk re-enrollment** at year rollover: pick the source class, mark passed, held back and transferred,
  and define the destination class.
- Student timeline: classes, final averages per year, attendance, incidents.
- **School history** as a PDF (for transfer), generated from the data.

## Notes

| Type | Example | Visible to |
|---|---|---|
| **Pedagogical** | "Improves a lot with pair activities" | The student's teachers and coordination |
| **Incident** | Lateness, behavior, conflict | Coordination, school and, if marked, guardians |
| **Praise** | "Helped classmates in the science project" | Teachers, coordination and guardians |
| **Reserved** | Delicate family situation | Only coordination and principal's office |

- Every note has an author, date and visibility; editing creates a new version (it does not erase the previous one).
- In the new year, the new teachers see the previous years' pedagogical notes: the "passing the baton" between teachers.

## What already works (M6.1: year rollover and timeline)

**Year rollover** screen (principal's office and coordination) and **History** tab in the student file.

- **A new year is born planned:** the school's first year is born open; the following ones stay closed ("planned") until the rollover, so as not to
  switch the current year mid-year. Only one year is open at a time.
- **1. New-year classes** (principal's office): creates the classes with the next grade (7th A becomes 8th A, 6th grade becomes 7th grade) and **copies the teachers**.
  After 9th grade there is no next class, and the students graduate. Whoever repeats needs a class of the same grade, created under Classes.
- **2. Bulk re-enrollment:** pick the source class and see each student with the **report card's suggestion** (passed, held back or pending, with the reason)
  and the likely destination class (same letter). Staff decide each student's outcome: **passed, held back, transferred or completed**.
  The operation is **all or nothing**: if one student is inconsistent, nothing is saved. Each decision goes in the audit log (`rematricula`).
  - Passed and held back get an enrollment in the new year's class; transferred and graduating students change the student's status.
  - **Grades, attendance and notes of the previous year stay tied to the old enrollment**, so the history is not lost.
- **3. Close the year and open the next:** requires every term to be closed (principal's office only). The new year becomes the current one.
- **Privacy at rollover:** only the **open** school year gives access to students and classes. After the year is closed, the teacher no longer sees the students
  who are no longer theirs, and the new teacher sees those of their class. (Guardians keep seeing their own children's history.)
- **Timeline:** one card per year, with class, result, **final averages and attendance per subject**. Principal's office and coordination see everything;
  **family and student see only what the teachers published**; **teachers see only class and result**, not other teachers' grades.

![Year rollover and bulk re-enrollment](/img/screenshots/virada-rematricula.png)

![Student timeline](/img/screenshots/linha-do-tempo.png)

## What already works (M6.2: notes)

**Notes** tab in the student file (staff and teachers; the student's account does not see notes).

| Type | Who creates | Who sees |
|---|---|---|
| **Pedagogical** | the student's teacher, coordination, principal's office | the student's teachers and coordination; **follows the student between years** |
| **Incident** | the student's teacher, coordination, principal's office | coordination, principal's office and whoever recorded it; **guardians only if marked** (and they are notified) |
| **Praise** | the student's teacher, coordination, principal's office | teachers, coordination and guardians (notified) |
| **Reserved** | only coordination and principal's office | only coordination and principal's office |

- **Versioning:** editing creates a **new version** and keeps the previous ones. The author and staff open the **edit history**; the family sees only the current version.
- **Passing the baton:** whoever becomes the student's teacher in the next year (open year) receives the **pedagogical notes and praise from all years**.
  Other teachers' incidents and reserved notes stay out of their reach. Whoever stops being the student's teacher sees nothing anymore.
- **Audit:** creating, editing and removing are recorded, and **each read of a reserved note by staff** generates `anotacao.reservada_lida`.
- **Removing** hides the note from everyone except staff (who see it faded), and the worker **deletes it for good, with its versions, after 30 days**.
- **Notices:** the family is notified of praise and of a visible incident, without the text in the notification; coordination is notified of incidents
  recorded by teachers.

![Notes seen by coordination](/img/screenshots/anotacoes-coordenacao.png)

![Edit history](/img/screenshots/anotacao-historico.png)

![Notes on the phone, seen by the family](/img/screenshots/anotacoes-familia-celular.png)

## What already works (M6.3: school history as a PDF)

On the **History** tab of the student file, the principal's office and coordination have the **Issue PDF** button, for school transfer.

- **Content:** school data, student name (and social name), date of birth and RA, and **one block per school year** with class, result, final average,
  attendance and result for each subject, plus overall attendance. It includes lines for **place and date** and **signature and stamp of the secretariat**.
- **What is not included:** notes, incidents, health data and CPF. Only what is needed for the transfer.
- **Who issues:** only staff. Families ask the school. That way the document comes out complete, not only with the published grades.
- **Record and verification code:** each issue records who issued it and when (`historico.emitir` in the audit log) and prints a **code** in the footer such as
  `06D5-D2C8-50F3`. The file lists the histories already issued.
- **Public verification:** at `/verificar/CODE` anyone confirms the code exists. The response shows **only the school, the date and the student's
  initials**, and no grades or date of birth. The code needs no login, but has 48 random bits (it cannot be guessed).
- **Validity:** the PDF is **informative** and says so. It counts as an official history after being **checked, signed and stamped by the secretariat**,
  as the model required by the school's education network.
- **No PDF library:** see [ADR 0005](../decisoes/pdf-proprio.md).

![Issuing from the student file](/img/screenshots/historico-emitir.png)

![First page of the PDF](/img/screenshots/historico-escolar-pdf.png)

![Public code verification](/img/screenshots/historico-verificar.png)

## Acceptance criteria (M6)

- [x] Enrollments per school year and bulk re-enrollment
- [x] Timeline
- [x] Notes with types, visibility and versioning
- [x] Pedagogical notes visible to the new teachers in the following year
