---
title: Access, invitations and 2FA
---

# Access, invitations and two-factor authentication

:::tip Delivered in M1
Everything on this page already works. The screenshots use the fictitious demo school.
:::

There is no open sign-up: **every account starts from an invitation** from the school. This ensures that only people the school
recognizes as a teacher, guardian or student get in.

![Sign-in screen](/img/screenshots/entrar.png)

## Invitations

1. The principal's office invites staff under **Staff → Invite** (teacher, coordination or principal/secretariat).
   Guardians are invited from the student's file (**Family** tab) or in bulk through the [spreadsheet import](./cadastro-de-alunos.md#spreadsheet-import).
2. The person receives an e-mail with a **single-use link valid for 7 days**. The screen also shows the link so the school can
   copy it and send it in a message if the e-mail does not arrive.
3. On opening the link, the person confirms their name and creates a password (minimum 10 characters, with letters and numbers).

![Invitation sent, with link to copy](/img/screenshots/equipe-convite.png)

<img src="/caderneta/img/screenshots/convite-celular.png" alt="Accepting an invitation on the phone" width="320" />

If the e-mail **already has an account** (e.g., a teacher who is also a student's mother), the invitation asks for the current password and only
**adds the new role** to the same account. She then chooses which role to enter with and can switch in the menu.

## Two-factor authentication (2FA)

Principal's office, secretariat and coordination see data on all students, so they **must** use 2FA. On first access,
Caderneta shows a QR code for an authenticator app (Google Authenticator, Microsoft Authenticator, 2FAS…) and only
unlocks the system after the first code is confirmed. On later logins, after the password, it asks for the code.

<img src="/caderneta/img/screenshots/configurar-2fa-celular.png" alt="2FA setup on the phone" width="320" />

Teachers, guardians and students can use 2FA but are not required to.

## Login protections

| Protection | How it works |
|---|---|
| Passwords | Argon2id; never stored in plain text |
| Wrong attempts | After 5 errors, progressive lockout (1, 2, 4… up to 60 minutes), also when accepting an invitation with an existing account |
| Non-existent e-mail | Same response and same timing as an existing e-mail (does not reveal who has an account) |
| Session | `HttpOnly`, `SameSite=Lax` cookie, expires after inactivity (12 h) and after 30 days |
| CSRF | The API refuses changes without the `X-Caderneta` header, which another site cannot send |
| Forgot password | Single-use link valid for 1 hour; when reset, all open sessions are ended |
| Audit | Login, failures, 2FA activation, accepted invitations and password changes are recorded |
