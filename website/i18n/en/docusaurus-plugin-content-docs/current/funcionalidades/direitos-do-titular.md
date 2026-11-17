---
title: Data subject rights
---

# Data subject rights (LGPD, arts. 18 and 19)

Everyone has the right to know what the school holds about them, to download a copy and to ask for correction or deletion. Caderneta offers this inside the app, on the **My data** page (also linked from **My account**).

## What each person can do

| Right | How it is met |
|---|---|
| **Confirmation and access** (art. 18, I and II) | **Instantly**, by themselves: *Download my data*. The file brings the content, origin, purposes, recipients and retention. It asks for the password again and is recorded in the audit log |
| **Portability** (art. 18, V) | The same file, in JSON (a structured, machine-readable format) |
| **Correction, deletion, information, withdrawal of consent** (art. 18, III, IV, VI to IX) | Request through the app, with a **protocol number and a 15 calendar-day deadline** (art. 19, II). The principal's office answers and the data subject follows along |
| **Who asks on behalf of a child** (art. 18, § 3) | The **guardian** downloads the child's data and makes requests about them. Guardian links marked as restricted do not have this access |

## What goes in the file (and what does not)

- **Included:** account, roles, links, notices read, authorizations answered, messages written by the person themselves, notifications; for the student: registration (including CPF), enrollments, **published grades**, attendance, praise and incidents visible to families, authorizations, histories issued and, **for the guardian only**, the health file.
- **Left out, to protect other people:** other guardians' contacts (name and type only), teachers' names, other people's messages.
- **Left out of the automatic file:** **pedagogical and reserved** notes. **Maintainer's decision:** they are only delivered **upon a request reviewed by the principal's office**, case by case, with a reasoned answer. The lawyer confirms this procedure in the opinion (gap T19).
- The **student's own account** does not receive the health file (it does not see it in the app either): the student asks the school.

## For the principal's office

The **LGPD requests** page (principal's and coordination menu) shows the queue ordered by deadline: *open*, *under review*, *fulfilled*, *partly fulfilled* or *not fulfilled*, with an **overdue** badge. Coordination follows along; **only the principal's office answers** and generates files.

- **Request received outside the app** (counter, e-mail, phone): the principal's office uses *Register request received outside the app* and enters the **date the school received it**; the deadline counts from it. The person asking does not need to know to call it a "data subject right": a request to "delete my registration" made through any channel is logged.
- **Generate data file:** the principal's office downloads the data subject's file to hand over to whoever asked. Generation is recorded.
- **Cancellation or deletion request:** the system **deletes nothing by itself**. The request stays **open** until a member of the principal's office reviews and answers on their own, in free text (there are no ready-made answers). That way each case considers what the school needs to keep.
- **Answering:** the answer is mandatory and explained. If it cannot be granted (for example, **the school history must be kept by law**, art. 16, I), the answer says why. The data subject is notified in the app.
- **Deletion:** the principal's office carries it out with the existing tools: [Leavers](./desligados.md) (delete now, with confirmation) for students who have left, and account anonymization for users. While the student is enrolled, the history stays and the rest can be deleted on request, per the opinion.
- Requests and answers are **kept as proof of compliance** (accountability, art. 6, X) for **5 years after the answer** and are then deleted by the worker. It is the period that covers damages claims and the ANPD's 5-year window for assessing recidivism, so the school can prove it complied. The LGPD does not set a period for this record. A request still open is never deleted. The school can change the period in the server configuration (`CADERNETA_RETENCAO_PEDIDOS_TITULAR_DIAS`).

## Security and privacy of the flow

- Downloading data requires the **password again**; wrong attempts count toward the account lockout.
- Only data the person could already see in the app, plus what the law guarantees (registration, CPF).
- Every export and every answer is recorded in the **audit log** (without the file's content).
- Each school only sees its own requests (per-school isolation in the database).

:::note Limits
This page describes the technical flow. Deadlines and what can be refused are a **legal decision**: the M8 opinion validates the procedure for internal notes and confirms that the legal basis (contract with the school, no consent) holds for all activities, which makes a consent-withdrawal flow unnecessary.
:::
