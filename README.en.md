# Caderneta

**Caderneta** is a lightweight, free-software school platform for Brazilian schools: grades and averages, attendance, notices and messages to families, calendar, exam printing, the student file and school history. It is built to be **private by default** (children's and health data) and to run on a small server.

- Documentation (Portuguese and English): <https://ettorecsenatore.github.io/caderneta/> (English: <https://ettorecsenatore.github.io/caderneta/en/>)
- Status: milestones M1 to M7 are done; M8 (security and compliance) has its code and documentation ready and is waiting for a lawyer's opinion and a penetration test; M9 (pilot) is being prepared. See the [roadmap](https://ettorecsenatore.github.io/caderneta/en/docs/roadmap).

## Quick start

See [Running locally](https://ettorecsenatore.github.io/caderneta/en/docs/tecnico/desenvolvimento). In short: `docker compose up -d` in `infra/`, then the API (`api/`, FastAPI + PostgreSQL with Row-Level Security) and the web app (`web/`, React PWA).

## Using it with a real school

- Deployment on one machine (Docker Compose + Caddy with automatic HTTPS): [Deployment](https://ettorecsenatore.github.io/caderneta/en/docs/tecnico/implantacao).
- **Before using real data**, generate the [lawyer package](https://ettorecsenatore.github.io/caderneta/en/docs/tecnico/pacote-juridico) (`python3 scripts/gerar-pacote-juridico.py`) and review it with the school's lawyer. The package and the legal texts in the app are in **Portuguese** because they apply Brazilian law (LGPD, ECA Digital).
- [Pilot plan](https://ettorecsenatore.github.io/caderneta/en/docs/piloto).

## License

Code: **GNU AGPL-3.0-or-later** (see [LICENSE](LICENSE)). Documentation and screenshots (fictitious data): **CC BY-SA 4.0** (see [LICENSE-DOCS.md](LICENSE-DOCS.md)). Third-party notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The name and logo "Caderneta" are not covered by those licenses.

Português: [README.md](README.md).
