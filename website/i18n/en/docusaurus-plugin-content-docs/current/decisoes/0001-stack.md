---
title: "ADR 0001: Stack"
sidebar_label: "ADR 0001: Stack"
---

# ADR 0001: FastAPI + PostgreSQL + React PWA

- **Status:** accepted (2026-11-15), implemented in M1
- **Context:** we need a lightweight web app, reachable in the browser and on the phone, with strong business rules
  (averages, permissions) and sensitive data. Small team, which already uses FastAPI and React in Sentinela do Fogo.

## Decision

| Layer | Choice | Alternatives considered |
|---|---|---|
| API | FastAPI + SQLAlchemy 2 + Alembic | Django (heavier, admin included); NestJS |
| Database | PostgreSQL 17 with Row-Level Security | SQLite (no RLS, hard for several schools) |
| Front end | React + Vite + TypeScript, PWA | SvelteKit (smaller, but the team has no experience); Next.js (SSR unnecessary) |
| Mobile | PWA first, Capacitor later ([ADR 0003](./0003-pwa-primeiro.md)) | React Native (a second codebase to maintain) |
| Queue | Procrastinate (Postgres) | Celery + Redis (one more service) |
| Deploy | Docker Compose + Caddy on a VM in Brazil | Kubernetes (overkill for the pilot) |

## Consequences

- A single database and few services: cheap and easy to back up.
- Reuses the knowledge and security patterns of Sentinela do Fogo.
- We must keep the React bundle lean (code splitting, no heavy UI libraries).

## Update (2026-11-17)

**The Procrastinate queue was not adopted**: background tasks (scheduled notices, e-mails, push, retention) run in a **simple worker** (`python -m app.cli notificar`, every minute), with no extra service. Deployment ended up as Docker Compose + Caddy (see [Deployment](../tecnico/implantacao.md)). The choice of hosting provider and region is still open.
