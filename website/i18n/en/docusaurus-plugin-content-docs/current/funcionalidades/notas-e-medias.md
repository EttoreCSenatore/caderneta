---
title: Grades and averages
---

# Grades and averages

:::tip Delivered in M2
Gradebook, configurable average engine, report card (screen and print/PDF), recovery, controlled publishing and
term closing already work. The screenshots use the fictitious demo school.
:::

The teacher enters the grades; Caderneta computes the averages with the school's rule and shows everything to students and
guardians as soon as the teacher publishes. **The average is never typed by hand.**

## Concepts

- **School year** divided into **terms** (two-month terms, three-month terms or semesters).
- **Gradebook**: one subject in one class (the teacher's assignment). Each gradebook has assessments and roll call.
- **Assessment**: exam, assignment, participation, mock exam or recovery, with a **weight**, a maximum value and an optional date.
- **Grade**: can be left blank (pending), marked as **excused** (`D`) or **excused absence** (`J`,
  the student will take a make-up). None of the three enters the average calculation.
- **Recovery**: an assessment marked as such; it acts according to the school's rule and **never lowers the average**.

## Entering grades

The teacher opens **Home → Grades** (or the class → Teachers → Open gradebook). Grades are in a grid: students in the
rows, assessments in the columns, average beside them.

![Term 3 gradebook](/img/screenshots/diario-notas.png)

- Type the grade (comma or dot accepted) and press **Enter** to go down to the next student.
- Each cell **saves itself**: it turns green when saved and red if the value is invalid or above the maximum.
- The student's average is recalculated instantly; below the passing average it appears in red.

![Grade saved and average recalculated](/img/screenshots/diario-lancamento.png)

![New assessment](/img/screenshots/diario-nova-avaliacao.png)

### Controlled publishing

Assessments start **unpublished**: the teacher enters grades calmly and clicks the **Unpublished → Published** badge
when finished. Students and families only see published assessments, and the average they see counts only those.

## Calculation rule

Each school sets the rule once per school year under **School → Average calculation rule**:

| Option | Choices |
|---|---|
| Term average | Weighted by the assessments' weights · Arithmetic |
| Annual average | All terms equal · Different weights per term (e.g., 2, 2, 3, 3) |
| Recovery | Replaces the average if higher · Mean between the average and recovery (if it raises it) · None |
| Rounding | One decimal place · To the nearest 0.5 · No rounding |
| Scale | 0 to 10, 0 to 100 or any maximum grade; grades from assessments with another value are converted |
| Passing | Minimum average and minimum attendance |

![Average calculation rule](/img/screenshots/regra-media.png)

```text
Example (weighted, passing 6.0, rounding to 0.5):
Exam 1 = 7.0 (weight 2) · Assignment = 9.0 (weight 1) · Exam 2 = 5.5 (weight 2)
Average = (7.0×2 + 9.0×1 + 5.5×2) / 5 = 6.8 → rounds to 7.0 ✅
```

The calculation lives in a pure API module (`api/app/medias.py`), with no database access, with table tests for each option.
Changing the rule recalculates all the year's averages immediately and is recorded in the audit log.

## Report card

The report card is the first tab of the student file. It shows, per subject, each term's average (with **R** when
recovery was applied), the annual average, absences, attendance and status. Clicking a subject shows
the grades of each assessment.

![Report card seen by the school](/img/screenshots/boletim.png)

On the phone, each subject becomes a card:

<img src="/caderneta/img/screenshots/boletim-celular.png" alt="Report card on the guardian's phone" width="320" />

**Print / save PDF** produces a clean version for paper (or PDF through the browser itself), with the school header,
no menus and no colors:

![Print version](/img/screenshots/boletim-impressao.png)

### Status

| Status | When |
|---|---|
| In progress | Year under way and average so far at or above the passing average |
| Below average | Year under way and average so far below the passing average |
| Passed / Failed | Only after **all terms are closed** |
| Failed for absences | Year closed and attendance below the minimum (75% by default, per the LDB) |

## Closing the term

Under **School**, coordination or the principal's office **closes** the term. Before that, the **Pending items** button shows, gradebook by gradebook,
assessments without grades, unpublished assessments and gradebooks with no class recorded.

![Term pending items](/img/screenshots/pendencias.png)

With the term closed, the teacher can only view. The **principal's office** can correct grades and roll calls in any gradebook
(**Correct this gradebook**), always with a justification: each change goes into the audit log with the before and after value.
Only the principal's office reopens a term.

![Closed-term gradebook](/img/screenshots/diario-fechado.png)

## Acceptance criteria (M2) ✅

- [x] Assessments with weight, maximum value, date and term
- [x] Entry grid with keyboard, autosave and validation
- [x] Configurable calculation engine with tests covering every option in the table
- [x] Report card for the student and the guardian, with highlights and controlled publishing
- [x] Term closing and correction by the principal's office with an audited justification
- [x] Report card for printing and PDF (through the browser; the server-generated PDF is left for the school history, in M6)

:::note Delivered later
- Entering grades **without internet**: done in M7, see [Offline mode](./offline.md).
- **Notifying the family** when a new grade comes out: done in M3, see [Communication](./comunicacao.md).
:::
