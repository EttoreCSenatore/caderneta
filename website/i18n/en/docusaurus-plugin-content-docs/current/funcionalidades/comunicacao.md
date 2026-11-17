---
title: Communication
---

# Communication: notices and messages

Replaces notes in the school planner and WhatsApp groups with channels that have the right recipient and read confirmation.

## Types

| Type | Who sends | Who receives | Reply |
|---|---|---|---|
| **School-wide notice** | School, coordination | The whole school, a segment or a group of classes | No (only "acknowledged") |
| **Class notice** | Teacher, coordination, school | Students and guardians of a class | No (only "acknowledged") |
| **Individual message** | Teacher, coordination, school | Guardians of a student (and the student, if the school allows) | Yes, in a conversation |
| **Authorization** | School, teacher | Guardians | I authorize / I do not authorize |

## Rules

- Notices can be marked **important**: they ask for an "acknowledged" confirmation and stay pinned until confirmed.
- The sender sees who has read and who has not; can resend a reminder to those pending.
- Individual messages stay in the student's history; coordination can follow teachers' conversations
  (transparency and protection for both sides).
- Attachments: PDF and images up to 10 MB, scanned by the antivirus before being stored.
- Scheduled sending (e.g., publish Monday at 7 a.m.).
- **Quiet hours**: e-mails outside the hours each person sets wait until the end of the quiet period (default 9 p.m. to 7 a.m.).

## Notifications

In order of cost: inside the app → push (PWA) → e-mail. WhatsApp and SMS remain an optional future integration,
because they have a per-message cost.

## What already works (M3.1: notices)

**Notices** screen in every role's menu.

- **Who sends:** principal's office and coordination send to the whole school or to any class; teachers send only
  to the classes they teach. Guardians and students only read.
- **Who receives:** class notices reach the guardians and students (with an account) of that class; school notices reach everyone.
  Guardians with a **restricted** link do not receive them.
- **Scheduling:** set "Publish at"; until then, only the author and staff see the notice, marked as scheduled.
- **Acknowledged:** the notice can ask for "I am aware". The reader sees the unread badge in the menu.
- **"Who read" panel:** the author (or staff) sees who read, who acknowledged and who is missing. The first timestamp is preserved.
- **Archive:** removes the notice from the inbox without erasing the reading history.

![Notice inbox seen by the principal's office](/img/screenshots/avisos-equipe.png)

![Reading panel](/img/screenshots/aviso-painel.png)

![Notice on the family's phone](/img/screenshots/avisos-familia-celular.png)

## What already works (M3.2: authorizations)

**Authorizations** screen for staff, teachers and guardians.

- **Who asks:** same rules as notices. Principal's office and coordination ask for the whole school or a class; teachers only for their classes.
- **Who answers:** only guardians, **per student** ("I authorize" or "I do not authorize"). Someone with more than one child at the school answers once per child.
  Restricted links do not see the request; the student's account does not answer either.
- **Deadline:** set by the author; after it, the answer is locked and the request appears as closed. Until then the family can change their mind.
- **Record:** each answer (and each change) is audited with who answered and when.
- **Panel:** the author sees who authorized, who refused and who has not yet answered, student by student.

![Authorization request on the phone](/img/screenshots/autorizacao-familia-celular.png)

![Answers panel](/img/screenshots/autorizacao-painel.png)

## What already works (M3.3: individual messages)

**Messages** screen for staff, teachers and guardians. Each conversation is about **one student**.

- **Who starts:** teacher (for students in their classes), principal's office and coordination (any student) and the guardian, who picks a
  teacher of the child's class.
- **Who takes part:** the school professional involved and the student's guardians without a restricted link. All of the student's guardians
  see the same conversation. The student's account does not take part.
- **Transparency:** principal's office and coordination can open any conversation; each access to someone else's conversation goes in the audit log
  (`conversa.supervisao`). Other teachers do not see it.
- **Unread:** badge in the menu and a "new" highlight in the list; opening the conversation marks it as read.

![Conversation seen by the principal's office](/img/screenshots/mensagens-conversa.png)

![Conversation list on the phone](/img/screenshots/mensagens-lista-celular.png)

## What already works (M3.4: notifications and alerts)

**Notifications** screen (menu and a bell at the top of the phone, with a counter of new ones).

- **In the app:** notices, authorizations, messages, published grade, absence alert and reminders generate a notification for whoever should see it.
  The sender is not notified of what they sent.
- **Minimal e-mail:** the e-mail **never carries the content**: it only says "you have N updates" and leads to the app. **One per person** goes out, bundling everything
  that accumulated. **Student accounts (minors) do not receive e-mail**, only notifications inside the app (privacy by default, ECA Digital art. 7).
- **Quiet hours:** default 9 p.m. to 7 a.m. in the school's time zone; each person adjusts it in **Preferences** and can turn e-mail off.
- **Scheduled notice:** the notification goes out at the set time, by the worker.
- **Remind pending:** on the notice, "Remind pending" notifies only those who have not yet read (or acknowledged, if the notice asks for it). At most
  **one reminder every 24 hours** per notice, audited.
- **New grade:** when an assessment is published, the family and the student with a grade entered are notified **only once**, without the grade value in the text.
- **Absence alerts:** when roll call is recorded, when the student reaches **15%** and then **20%** absences in the year (all subjects,
  counting excused absences, as on the report card), the family and coordination are notified. Each level fires only once per enrollment.
- **Retention:** read notifications are deleted after **90 days** and any notification after **180**.

### Worker

E-mail, scheduled notices and retention run from one command, meant for cron every minute:

```bash
.venv/bin/python -m app.cli notificar
```

![Notice with reminder to those pending](/img/screenshots/aviso-lembrete.png)

![Notifications and preferences](/img/screenshots/notificacoes.png)

![Notifications on the phone](/img/screenshots/notificacoes-celular.png)

### Attachments in messages

In conversations you can attach up to **3 files** (PDF, JPG or PNG, 10 MB each), for example a medical certificate.

- Photos are sent **without EXIF**: location, date and device model are removed before storing.
- Every attachment goes through the antivirus, is **encrypted**, and is downloaded through a **5-minute signed link** bound to the user. Each download is audited
  (`mensagem.baixar`), including when coordination supervises the conversation.
- Only conversation participants open the attachment. After 365 days the attachment is deleted and the message text remains.

![Attachment in a conversation](/img/screenshots/mensagem-anexo.png)

## Push on the device (M3.5)

A notification on the phone or computer, even with the app closed. Under **Notifications > Device notification (push)** the person taps **Enable on this device**.

- **No content:** the push message goes **empty**, signed with VAPID. The device always shows the same notice ("You have news. Tap to open.") and the app
  opens on Notifications, where the text sits behind the login. **Nothing about the student passes through Google, Apple or Mozilla**, and the server does not store the device's
  encryption keys (only the push service address).
- **Who receives:** guardians and staff. **Student accounts (minors) do not receive push**, only the in-app notifications, as with e-mail.
- **Activation:** only when the person clicks (the browser asks for permission). The basis is performance of the service contracted with the school, with no extra consent flow,
  and the person can turn it off whenever they want.
- **Quiet hours:** same as e-mail (default 9 p.m. to 7 a.m.). A device receives **one push** per round, even with several news items.
  Someone who has already read the notification is not notified.
- **Device retention:** the subscription is deleted on **disabling**, on **signing out of the app** (several users can share the same browser), when the push service says the
  device **no longer exists**, after **90 days without use** and when the **account is deactivated**.
- **Security:** the device address is only accepted if it belongs to a known push service (Google, Apple, Mozilla, Microsoft), over HTTPS, which prevents the server from being used
  to call internal addresses. Each subscription and cancellation goes in the audit log.
- **Server activation:** `python -m app.cli gerar-vapid` generates the keys, which go in the environment (`CADERNETA_VAPID_PRIVATE_KEY` is a secret). Without keys, push is off.
- **iPhone:** only works with the app installed on the home screen (iOS 16.4 or newer). For other cases e-mail keeps covering.

## Acceptance criteria (M3)

- [x] Notices for the whole school and per class, with scheduling (M3.1)
- [x] Individual messages in a conversation (M3.3); attachments left for M5, together with file storage
- [x] "Acknowledged" confirmation and reading panel for the sender (M3.1)
- [x] Digital authorizations with a recorded answer (M3.2)
- [x] In-app notifications and e-mail with quiet hours (M3.4); push left for later
