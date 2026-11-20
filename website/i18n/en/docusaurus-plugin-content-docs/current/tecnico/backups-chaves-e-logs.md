---
title: Backups, keys and logs (M8.5)
---

# Backups, keys and logs

Safe operation of an installation with real data. Applies to whoever hosts (the operator or the school itself).

## Data keys

The data key (`CADERNETA_DATA_KEY`, AES-256) encrypts the **health file**, the **2FA secrets** and the **files** (exams and attachments).

- **Keep it off the server**, in a secrets vault or an offline place, with a separate copy. **Without the key, the encrypted data does not open**, not even in backups.
- **One key per installation** and per environment (never reuse the production one in tests).
- **Rotation** (every year, or immediately if a leak is suspected):
  1. generate a new key (base64 of 32 bytes) and put it in `CADERNETA_DATA_KEY`; the old one goes to `CADERNETA_DATA_KEYS_ANTIGAS`;
  2. restart the API. It now **reads with both** and **writes with the new one**;
  3. run `python -m app.cli rotacionar-chave --simular` to see what is left and then `python -m app.cli rotacionar-chave` (you can repeat it, it is safe) until nothing remains;
  4. only then remove the old key from the configuration. **Keep it as long as backups made with it exist.**
- Signed links (5 minutes) use only the current key: when you switch, open links expire.

## Encrypted backups

Scripts in `infra/backup/` (they need `pg_dump`, `pg_restore`, `psql` and `gpg`):

- **`backup.sh`** produces a `caderneta-<date>.tar.gpg` file with the **database** and the **files directory**, encrypted with AES-256 by a **backup password** (a different one, not the data key) and with checksums. It deletes backups older than 35 days (`RETENCAO_DIAS`).
- **`restore-test.sh`** runs the **restore test**: opens the backup, checks the checksums, restores into a **temporary** database, counts the data and checks that the **data keys open** the health file, the 2FA and the files, and that **no file is missing**. It fails if the password is wrong, the backup is corrupted or the key does not open.
- **Run the restore test for every new backup, at least once a month**, and record the result. A backup that was never restored is not a backup.
- Keep the backup **somewhere other than** the server (another account or region) and the backup password **separate** from it.

### Retention and deletions (T24)

- A backup **expires by itself within 35 days**: what the school deleted (a student who left, a deletion request) disappears from the backups within that period.
- If you really have to **restore**, what was deleted after the backup **comes back**. After restoring: run `python -m app.cli notificar` (re-applies the leavers' retention and the periods) and ask the principal's office to **review the deletion requests** made after the backup date and redo them. The privacy policy says backups expire in their own cycle.

## Logs without personal data

- The application **does not log** request content, names or e-mails.
- The **server's access log** used to keep the whole URL. It now **strips the query string** (for example, a search by student name) and **replaces with a marker** the secrets that travel in the URL (invitation, calendar link, history verification code). The **IP** stays, because it is the access record and the basis for investigating incidents; the retention period is an opinion decision (T5).
- If a reverse proxy sits in front, apply the same rule to it: **do not log the query string or those paths**.
- Run the API with `--proxy-headers --forwarded-allow-ips=<proxy IP>` so the attempt limit sees the real IP.

## Monitoring and alerts

The script `deploy/verificar.sh` (for cron, every 10 minutes) checks: `/api/saude` is up, **late backup** (stale `ultimo-backup.txt`), **full disk**, database responding and **stopped service**; if anything fails, it alerts the on-call person through an alert URL (ntfy, healthchecks.io etc.). See [Deployment](./implantacao.md). Still to configure: an alert for 5xx errors and for **many login failures** (`login_falhou` actions in the audit log). Whoever receives the alert is the technical on-call person (see the incident plan).


### Warnings inside the app (MO.4)

The school management (administrator role) sees a yellow banner at the top of every screen when something in the installation needs attention, to pass on to whoever looks after the server:

| Warning | When | Setting |
|---|---|---|
| **Backup** | no backup recorded, or the last one is older than 26 hours | `CADERNETA_BACKUP_MAX_HORAS` |
| **Restore test** | no test recorded, or the last one is older than 40 days | `CADERNETA_RESTAURACAO_MAX_DIAS` |
| **Disk** | the disk holding the files reached 85% | `CADERNETA_DISCO_MAX_PCT` |
| **Memory** | the server's memory in use reached 90% | `CADERNETA_MEMORIA_MAX_PCT` |

- **Recording backups:** `backup.sh` and `restore-test.sh` record each successful run in the database when given `REGISTRAR` (the CLI command inside the `worker` container, see `deploy/cron.exemplo`). The record keeps only the date, the file name and the size; there is no personal or school data. The app only reads it; the CLI writes it, with the database owner role.
- **On only in production:** the backup and restore warnings apply when `CADERNETA_ENV=prod` (or `CADERNETA_BACKUP_MONITORADO=true`). Disk and memory always apply.
- **How it measures:** disk from the files folder (`CADERNETA_STORAGE_DIR`) and memory from `/proc/meminfo`, at the moment the page asks (`GET /api/operacao`, management only). There is no background collection and no Docker access.
- **It does not replace the on-call alert:** `verificar.sh` alerts even with the app down; the banner is a second layer for people who use the app every day.

:::note Limits
**Not yet verified in production**: the hosting was not chosen. The scripts were tested with the development database in a container.
:::
