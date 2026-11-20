---
title: Deployment
---

# Production deployment

A recipe to put an installation online on **one machine** (any provider that runs Docker): PostgreSQL database, antivirus, API, worker and the site with **automatic HTTPS**. It applies to one school or to an operator that serves several (one installation per school is the simplest way to isolate them).

:::caution Real data only after M8
To go live with **real student data**, the installation must have gone through the [lawyer package](./pacote-juridico.md), the legal opinion and the [pilot plan](../piloto.md). Without that, use only fictitious data (demo).
:::

## What comes up

| Service | What for |
|---|---|
| `web` (Caddy) | Serves the app, does the **HTTPS** (Let's Encrypt) and the `/api` proxy; sends the security headers (CSP, HSTS...); log **without path or query string** |
| `api` | The API (FastAPI) with the restricted database role (RLS applies) |
| `worker` | Every minute: scheduled notices, e-mails, push, **retention and deletion of leavers** |
| `migrate` | Runs the migrations with the owner role and exits |
| `db` | PostgreSQL 17 |
| `clamav` | Antivirus for attachments (**mandatory** in production) |

Only `web` publishes ports (80 and 443). Database, API and antivirus stay on the internal network.

## Step by step

1. **Machine:** Linux with Docker and Docker Compose, with a name (DNS) pointing to it and ports 80 and 443 open. At least 2 GB of memory (the antivirus uses more than 1 GB).
2. **Code:** clone the repository and enter `deploy/`.
3. **Configuration:**

   ```bash
   cp .env.example .env
   sh gerar-segredos.sh                  # prints database passwords and the data key: paste the values into .env
   ```

   Fill in the domain, certificate e-mail, **operator** (name and contact), and the SMTP of the e-mail provider. **Keep a copy of `.env` and of the data key off the server**: without the key, the encrypted data does not open, not even in backups.
4. **Start:**

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

   The first start downloads the antivirus virus database (a few minutes); the API only starts when it is ready.
5. **First school and administrator:**

   ```bash
   docker compose -f docker-compose.prod.yml exec api python -m app.cli criar-escola "School Name" direcao@escola.com.br "Principal's Name"
   ```

   The invitation arrives by e-mail; the principal sets the password and configures 2FA.
6. **Smoke test:** `sh smoke.sh https://your-domain` checks the site, the API, the security headers, CSRF and the public privacy policy.
7. **Backups and monitoring:** copy `cron.exemplo` into the `crontab` and adjust: **daily encrypted backup**, **monthly restore test** and `verificar.sh` every 10 minutes (site down, late backup, full disk, stopped database or service), alerting the on-call person through `ALERTA_URL` (ntfy, healthchecks.io etc.). See [Backups, keys and logs](./backups-chaves-e-logs.md).
8. **The school's legal texts:** if the lawyer approved own texts, put `privacidade.md` and `termos.md` in `deploy/legal/` and uncomment `CADERNETA_LEGAL_DIR=/legal` in `.env`.

## Updating

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
sh smoke.sh https://your-domain
```

What changed in each version is in [`releases.yaml`](https://github.com/EttoreCSenatore/caderneta/blob/main/releases.yaml) and the [GitHub releases](https://github.com/EttoreCSenatore/caderneta/releases); the smoke test shows the version running (see [Versions and What's new](./versoes.md)). Migrations run by themselves (`migrate`). **Take a backup before** updating. To go back, restore the backup and the previous version of the code.

## Machine security (the host's responsibility)

- Automatic operating-system security updates; access by **SSH key**, no password; firewall allowing only 22 (restricted), 80 and 443.
- **Encrypted** server disk (volume), when the provider offers it.
- Backups **somewhere else** (another account or region).
- Whoever has access to the server can see the database and the keys: limit and record those accesses (see the [incident plan](./documentos-de-conformidade.md)).

## Known limits

- This recipe was **tested locally** (full stack with test HTTPS), **not** on real hosting: the pilot's hosting has not yet been chosen.
- DOCX-to-PDF conversion (LibreOffice) **is not in the image**: DOCX exam attachments must be uploaded as PDF until it is decided to include it.
- High availability, multiple machines and S3 for files are left for after the pilot.
