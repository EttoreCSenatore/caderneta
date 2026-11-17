---
title: Calendar
---

# School calendar

A layered calendar: the school defines what applies to everyone; the teacher adds what applies to their classes.

## Layers

| Layer | Who edits | Who sees | Examples |
|---|---|---|---|
| **School (general)** | School | Everyone | Holidays, recesses, start and end of term, parent meeting, June festival |
| **Days off** | School | Everyone | Holiday, bridge day, class council, strike, outside event |
| **Class** | Teacher (their classes), coordination, school | The class and its guardians | Math exam, assignment due date, field trip |

## Features

- When the school year is created, **national holidays** are suggested automatically; the school confirms and adds the state and municipal ones.
- **Month**, **week** and **list** views (list is the default on the phone).
- Events colored by type: holiday, day off, assessment, event, deadline.
- **Assessments** created in [Grades and averages](./notas-e-medias.md) with a date show up on their own on the class calendar.
- Automatic notice to guardians when the school registers a day off.
- **iCal** export to subscribe in Google Calendar or the phone's calendar.

## What already works (M4)

**Calendar** screen for every role, with **List** (default on the phone), **Month** and **Week** views.

- **Who sees:** the school sees everything; teachers see the school's events and their classes'; guardians and students see the school's events
  and their children's classes' (a restricted link does not see). Staff and teachers can filter by class.
- **Who creates:** principal's office and coordination create school events, events for any class, **holidays** and **days off**. Teachers create
  an event, assessment and deadline only in the classes they teach, and edit or delete only what they created.
- **Dated assessments** (in [Grades and averages](./notas-e-medias.md)) show up on their own on the class calendar, read-only.
- **National holidays:** the **Holidays** button (principal's office/coordination) lists the year's dates to confirm. The nine statutory national holidays
  come checked: Law 662/1949 (as worded by Law 10.607/2002), Law 6.802/1980 (Oct 12) and Law 14.759/2023 (Nov 20). Carnival, Good Friday
  and Corpus Christi (movable dates, calculated from Easter) stay unchecked, since the school decides. State and municipal holidays are
  registered as an event. Importing again does not duplicate.
- **A day off and a holiday block roll call** on those dates (new roll call or a date change), with a message explaining why. A day off
  for just one class does not block the others. Classes already recorded on those dates **are not erased**: staff receive the count to review.
- **Notice to families:** when a day off is registered, the families and students in the audience are notified (see [Communication](./comunicacao.md)).
- **iCal subscription:** the **Subscribe** button generates a link for Google Calendar or the phone's calendar. The link is a credential: it appears **once**,
  only the hash is stored, generating another drops the previous one, and it can be turned off. The subscribed calendar shows the events with the class name in front,
  **without student names**.

![Month calendar](/img/screenshots/calendario-mes.png)

![Holidays of the year](/img/screenshots/calendario-feriados.png)

![iCal subscription](/img/screenshots/calendario-assinar.png)

![List on the phone](/img/screenshots/calendario-lista-celular.png)

Left for later: events with a time of day, recurrence (e.g., every Monday) and pre-loaded state and municipal holidays.

## Acceptance criteria (M4)

- [x] School calendar editable by the school, with national holidays pre-loaded (confirmed by the school)
- [x] Class events created by teachers, visible only to the class
- [x] Days off block roll call and notify families
- [x] Month/week/list views and iCal export
