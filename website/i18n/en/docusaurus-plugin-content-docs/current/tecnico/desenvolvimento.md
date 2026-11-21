---
title: Running locally
---

# Running locally

Requirements: Docker, Python 3.13+ and Node 24+.

## 1. Database and test e-mail

```bash
cd infra
docker compose up -d        # Postgres at 127.0.0.1:5433 and Mailpit at http://localhost:8025
```

The script `infra/postgres/init/01-roles.sh` creates two roles: `caderneta_owner` (owner of the tables, used only by
migrations and the seed) and `caderneta_app` (used by the API, subject to Row-Level Security). Invitation and
password-recovery e-mails show up in Mailpit.

## 2. API

```bash
cd api
python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head      # creates the tables and the RLS policies
.venv/bin/python -m app.seed         # fictitious demo school
.venv/bin/uvicorn app.main:app --reload --port 8000
.venv/bin/pytest                     # tests (use the caderneta_test database)
```

Interactive API documentation at `http://localhost:8000/api/docs` (off in production).

## 3. Web app

```bash
cd web
npm ci
npm run dev       # http://localhost:5173 (forwards /api to port 8000)
npm test
npm run build
```

## Documentation screenshots

With the API and web app running and the seed applied:

```bash
cd web
npm run screenshots          # all
npm run screenshots -- m2    # a single group (m1, m2, m3, m4, m5, m6, desligados...)
```

Images go to `website/static/img/screenshots/`. The script fails if any error shows up in the browser console.

## End-to-end tests of offline mode

With the API and seed running and the build served (`npm run build && npx vite preview`, port 4173):

```bash
cd web && npm run e2e:offline    # real Chromium, service worker, internet cut
```

## Demo accounts

The seed creates the fictitious school **Colégio Horizonte (demonstração)** with 136 randomly generated students. The accounts and the demo
password are documented at the top of `api/app/seed.py`. The principal's office and coordination use 2FA:
`python -m app.seed --codigo` shows the current code. The seed refuses to run with `CADERNETA_ENV=prod`.

## Creating a real school

```bash
.venv/bin/python -m app.cli criar-escola "School Name" direcao@escola.com.br "Principal's Name"

# notification worker (scheduled notices, e-mails, retention); in production, run it every minute
.venv/bin/python -m app.cli notificar
```

Creates the school and sends the first administrator's invitation.

Other useful commands (`python -m app.cli ...`): `revogar-sessoes [escola_id]` (incident response), `rotacionar-chave [--simular]` (data key rotation), `gerar-vapid` (push keys).

## Production, backups and the lawyer package

- Deployment: [Deployment](./implantacao.md) (`deploy/`).
- Backups and keys: [Backups, keys and logs](./backups-chaves-e-logs.md) (`infra/backup/`).
- Lawyer package: [Lawyer package](./pacote-juridico.md) (`scripts/gerar-pacote-juridico.py`).

## Environment variables

| Variable | Purpose |
|---|---|
| `CADERNETA_DATABASE_URL` | API connection (role `caderneta_app`) |
| `CADERNETA_OWNER_DATABASE_URL` | Migrations, seed and CLI (owner role) |
| `CADERNETA_DATA_KEY` | AES-256 key in base64 for sensitive data (**mandatory in production**) |
| `CADERNETA_ENV` | `dev`, `test` or `prod` |
| `CADERNETA_PUBLIC_URL` | Web app address, used in the links of e-mails |
| `CADERNETA_COOKIE_SECURE` | `true` in production (mandatory) |
| `CADERNETA_SMTP_*`, `CADERNETA_MAIL_FROM` | E-mail sending |
| `CADERNETA_OPERADORA_NOME`, `CADERNETA_OPERADORA_CONTATO` | Who operates this installation (appears in the policy and terms) |
| `CADERNETA_LEGAL_DIR` | Folder with own legal texts (`privacidade.md`, `termos.md`) |
| `CADERNETA_DATA_KEYS_ANTIGAS` | Old keys, only to read during rotation |
| `CADERNETA_RATE_LIMIT`, `CADERNETA_TOTP_ANTI_REUSO` | On by default; off only in tests that do not exercise them |

Generate a key: `python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`.
Keep it outside the database and the repository: without it, the health files cannot be read.

## File storage

Exams and assignments stay encrypted in `CADERNETA_STORAGE_DIR` (default `./storage`, already in `.gitignore`). In production the path
must be absolute, outside the code, readable only by the API user and **inside the backup**. See
[ADR 0004](../decisoes/armazenamento-de-arquivos.md). Adjust the limit with `CADERNETA_MAX_ARQUIVO_BYTES`.

Optional in development (in production the antivirus is mandatory):

| Variable | Effect |
|---|---|
| `CADERNETA_ANTIVIRUS=clamav` | scans every upload with `clamd` (`docker compose --profile antivirus up -d clamav`, port 3310) |
| `CADERNETA_CONVERSOR=libreoffice` | converts DOCX to PDF on upload (needs `soffice` installed) |
| `CADERNETA_RETENCAO_PEDIDOS_DIAS`, `..._RASCUNHO_DIAS`, `..._ANEXOS_DIAS` | deletion periods (365, 90, 365) |

## Database migrations

Every database change is an Alembic migration in `api/migrations/versions/` (`alembic revision -m "what changes"`), numbered in sequence and with `upgrade()` **and** `downgrade()`.

- **Round trip:** `api/tests/test_migracoes.py` goes up the migrations one by one saving each version's schema (tables, columns, indexes, constraints, RLS, policies, functions, types, triggers and the app role's privileges), then goes down one by one and compares at every step. A `downgrade()` that forgets something fails the test and says what was left over or went missing.
- **Report on the PR:** when a PR touches `api/migrations/`, the *Migrations* workflow comments on the PR with the SQL of each new migration (Alembic offline mode, no database) and points out what needs attention: dropping a table or column, deleting rows, changing a type, renaming, requiring a value, revoking a privilege, disabling RLS, and already published migrations that were changed. Locally: `python3 scripts/relatorio-migracoes.py --base origin/main --saida relatorio.md`.
- **A published migration does not change:** its `upgrade()` has already run on real databases. Fix it with a new migration. Only `downgrade()` may be repaired, as was done in 0001 (RLS policies now go before the tables).
- **SQL without running:** `alembic upgrade 0016:0017 --sql` prints the SQL of one step.

## Documentation in two languages

The documentation site is **bilingual**: Portuguese lives in `website/docs/` and **English** in `website/i18n/en/docusaurus-plugin-content-docs/current/` (same file names). **Every documentation change updates both versions.** CI runs `python3 scripts/checar-traducao.py`, which fails if an English page is missing or if the structure (headings, code blocks, images) diverges. To see the English locally: `cd website && npm run build && npm run serve` (the language switcher is at the top). The app's legal texts and the `.lgpd/` artifacts stay **in Portuguese only**, because they apply Brazilian law.
