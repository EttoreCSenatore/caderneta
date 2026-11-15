---
title: "ADR 0001: Stack"
sidebar_label: "ADR 0001: Stack"
---

# ADR 0001: FastAPI + PostgreSQL + React PWA

- **Status:** proposta (2026-11-15), aguardando confirmação
- **Contexto:** precisamos de um web app leve, acessível no navegador e no celular, com regras de negócio fortes
  (médias, permissões) e dados sensíveis. Equipe pequena, que já usa FastAPI e React no Sentinela do Fogo.

## Decisão

| Camada | Escolha | Alternativas consideradas |
|---|---|---|
| API | FastAPI + SQLAlchemy 2 + Alembic | Django (mais pesado, admin pronto); NestJS |
| Banco | PostgreSQL 17 com Row-Level Security | SQLite (sem RLS, difícil para várias escolas) |
| Front | React + Vite + TypeScript, PWA | SvelteKit (menor, mas equipe sem experiência); Next.js (SSR desnecessário) |
| Celular | PWA primeiro, Capacitor depois ([ADR 0003](./0003-pwa-primeiro.md)) | React Native (segundo código para manter) |
| Fila | Procrastinate (Postgres) | Celery + Redis (mais um serviço) |
| Deploy | Docker Compose + Caddy numa VM no Brasil | Kubernetes (exagero para o piloto) |

## Consequências

- Um só banco e poucos serviços: barato e fácil de fazer backup.
- Reaproveita o conhecimento e os padrões de segurança do Sentinela do Fogo.
- Precisamos manter o bundle do React enxuto (code splitting, sem bibliotecas de UI pesadas).
