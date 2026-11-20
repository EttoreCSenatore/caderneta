---
title: Security review (M8.1)
---

# Code security review (M8.1)

An internal review, done by reading the code, automatic tools and tests. It **does not replace** the third-party penetration test or the legal opinion, which remain in the closing of M8.

## What was checked and the result

| Topic | Result |
|---|---|
| **Dependencies** | `pip-audit` and `npm audit` with no known vulnerabilities; they run in CI on every change. CI generates the **SBOM** (CycloneDX) of the API and the web app as an artifact |
| **Supply chain** | **Dependabot** proposes updates in grouped PRs, with a 7-day wait for new versions (security fixes arrive right away). **Actions** are pinned to a commit and **Docker images** by digest; `scripts/checar-fixacao.py` fails CI if something comes in unpinned or if the same image differs between CI, development and production |
| **Static analysis** | `ruff` with security rules (`S`, Bandit style) with no findings; no SQL built from text with user data (everything through the ORM or parameters) |
| **Secrets in the repository** | No `.env` file, key or token versioned. The demo values (seed password and 2FA secret) are fictitious and exist only in the local environment |
| **Authentication** | Argon2id passwords; constant time even for a non-existent e-mail; progressive lockout per account; session with an opaque token (only the hash in the database), `HttpOnly`, `SameSite=Lax` cookie and `Secure` mandatory in production; 2FA mandatory for staff |
| **Authorization** | Role and link checked in the API and, underneath, **Row-Level Security** in PostgreSQL. A test walks **every route** and fails if any is left without login outside the known public list (7: sign-in, password recovery, invitation, iCal by secret link and history verification) |
| **CSRF** | `X-Caderneta` header required on every request that changes data, with no CORS enabled |
| **Uploads** | Validated by content, antivirus (fail closed), EXIF removed, encrypted at rest, download through a 5-minute signed link |
| **API headers** | `nosniff`, `no-store`, `no-referrer`, `X-Frame-Options: DENY`, `Cross-Origin-Resource-Policy`, empty CSP on JSON responses and **HSTS** in production |

## What was fixed in this stage

- **Rate limiting** (there was none before): login per IP (30 every 15 min), password recovery (3 per e-mail and 20 per IP per hour, **always answers 204** so as not to reveal whether the e-mail exists), reset, invitations and the public history verification (20 per minute per IP; before, only the code length protected it). The counter is stored with a **hash** of the IP or e-mail, never the value, and is deleted after 2 days
- **A 2FA code is not valid twice**: someone who peeks at the 6-digit code cannot reuse it within the same 30-second interval
- **User account** (new *My account* page): change password (asks for the current one, drops the other sessions), see the **connected devices** and **sign out of all devices**, which also cancels push on all of them. This is the procedure for a lost or lent phone
- New security headers on the API and HSTS in production

## Resolved later (M8.5 and M9)

- **Site headers:** the Caddy of the [deployment](./implantacao.md) sends CSP, HSTS, `nosniff`, `Referrer-Policy` and `Permissions-Policy`, and its log keeps neither path nor query string (verified in the browser, with no CSP violation).
- **Reverse proxy and real IP:** the API image runs with `--proxy-headers`, and only the proxy reaches the API.
- **Data key rotation:** done (`rotacionar-chave`); see [Backups, keys and logs](./backups-chaves-e-logs.md).

## Left for the closing of M8 and for the real deployment

- **Third-party penetration test**, before the pilot.
- **2FA for teachers:** today it is mandatory only for staff (maintainer's decision). Teachers see names, grades, notes and messages (but only the health **summary alert**). Revisit in the legal opinion and the RIPD.
- **Passwords:** there is no list of leaked or common passwords (only minimum length and mixing of character types).
- **2FA recovery** (phone lost by staff): today it depends on the principal's office redoing the access; a flow with backup codes is missing.
- **Monitoring and alerts:** the tool exists (`deploy/verificar.sh`); it still has to be configured on the real hosting.

## OWASP Top 10 checklist (2021)

| Item | Status |
|---|---|
| A01 Broken access control | Covered (role + link + RLS + test of all routes). The pen test confirms |
| A02 Cryptographic failures | Argon2id, AES-256-GCM for health and files, TLS at deployment, key rotation done |
| A03 Injection | ORM and parameters; no `ruff S` findings |
| A04 Insecure design | Privacy by design; rate limits added |
| A05 Security misconfiguration | Production requires key, ClamAV, secure cookie and absolute path; API documentation off; the app's Caddy sends the headers |
| A06 Vulnerable components | `pip-audit` and `npm audit` in CI, Dependabot, SBOM and license audit |
| A07 Authentication failures | Lockout, 2FA, per-IP limit, no code reuse. Missing: weak-password list and backup codes |
| A08 Software and data integrity | Dependencies pinned by lock; history issued with a verification code |
| A09 Logging and monitoring failures | Audit of sensitive actions and login. Check script ready; to be configured on the hosting (M9) |
| A10 SSRF | The only access to an external address coming from user data is push, with an allow-list of hosts |
