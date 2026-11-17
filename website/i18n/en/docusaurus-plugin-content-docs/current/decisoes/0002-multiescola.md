---
title: "ADR 0002: Multiple schools"
sidebar_label: "ADR 0002: Multi-school"
---

# ADR 0002: One installation, several schools, isolated in the database

- **Status:** accepted (2026-11-15)
- **Context:** the pilot will be with one school, but the platform must serve several without reinstalling everything. Data leaking
  between schools is the worst possible risk.

## Decision

- A single database; every school table has `escola_id` (school id).
- **Row-Level Security** in PostgreSQL: the API sets `app.escola_id` and `app.usuario_id` per transaction, and the policies
  only return rows of that school. The database user used by the API does not own the tables and does not bypass RLS.
- Automated tests try to read another school's data on every endpoint.

## How it turned out in M1

- Functions `app_escola()` and `app_usuario()` read the transaction variables; the API sets them with `set_config(..., true)`,
  which only last until the end of the transaction.
- Special policies: `usuario` (user) is visible if it is the person themselves, if they have a role or link at the active school, or if it is the
  e-mail in the middle of a login; `convite` (invitation) is also visible by the hash of the token in use; `escola` (school) can only be created by the owner
  role (CLI `python -m app.cli criar-escola`).
- The API cannot change or delete the `auditoria` (audit) table (insert only).
- With no context set, the API role sees no rows at all (tested in `api/tests/test_isolamento.py`).

## Consequences

- A large school can, in the future, get its own database without changing the code.
- Migrations must always create the RLS policy together with the table (checked in CI).
