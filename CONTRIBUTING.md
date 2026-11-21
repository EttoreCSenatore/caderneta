# Como contribuir / Contributing

🇧🇷 Português | [🇺🇸 English](#english)

Obrigado pelo interesse na Caderneta. Contribuições são bem-vindas: correções, melhorias, documentação e traduções.

## Antes de começar

- **Falha de segurança?** Não abra issue: siga o [SECURITY.md](SECURITY.md).
- **Ideia ou mudança grande?** Abra uma issue antes, para combinar o caminho. O [roadmap](https://ettorecsenatore.github.io/caderneta/docs/roadmap) mostra o que já está planejado.
- Ao participar, você concorda com o [Código de Conduta](CODE_OF_CONDUCT.md).

## Ambiente

Siga [Como rodar localmente](https://ettorecsenatore.github.io/caderneta/docs/tecnico/desenvolvimento): Postgres e Mailpit no Docker, API em FastAPI, app web em React. O `python -m app.seed` cria uma escola fictícia com contas de cada papel.

## Regras do projeto

- **Um assunto por PR.** A branch `main` é protegida: todo PR passa pela CI (lint, testes com Postgres real, auditoria de dependências e licenças, build das imagens) e é integrado com *squash*.
- **Testes:** mudança de comportamento vem com teste. API: `cd api && .venv/bin/pytest`. Web: `cd web && npm run typecheck && npm test`.
- **Estilo:** `ruff check` e `ruff format` na API (linha de 120); TypeScript estrito no web.
- **Isolamento entre escolas:** toda tabela nova com dados de uma escola precisa de `escola_id` e de política de Row-Level Security. O teste `test_diario.py` reprova tabela sem RLS.
- **Dados pessoais (LGPD):** um PR que coleta um dado pessoal novo atualiza o mapa de dados e as lacunas em [`.lgpd/`](.lgpd/). Nunca use dados reais em testes, screenshots ou issues.
- **Documentação em duas línguas:** toda mudança na documentação (`website/docs/`) atualiza também a versão em inglês (`website/i18n/en/...`). A CI reprova se as duas divergirem (`scripts/checar-traducao.py`). Os textos legais do app e os artefatos de `.lgpd/` ficam só em português.
- **Dependências:** prefira não adicionar. Se precisar, a licença tem que ser compatível com a AGPL (`scripts/auditar-licencas.py`), e Actions e imagens Docker entram fixadas por commit e digest (`scripts/checar-fixacao.py`).
- **Migrations:** toda migration tem `downgrade()` que desfaz tudo (o teste `test_migracoes.py` confere passo a passo); migration já publicada não muda, corrige-se com uma nova. O PR recebe um relatório com o SQL e as operações que apagam dados.
- **Versões:** um PR que muda algo para quem usa acrescenta o item no topo do [`releases.yaml`](releases.yaml) e sobe a versão em `api/pyproject.toml` e `web/package.json` ([Versões e Novidades](https://ettorecsenatore.github.io/caderneta/docs/tecnico/versoes)).
- **Interface em português do Brasil**, com linguagem simples: quem usa é professor, família e aluno.

## Licença das contribuições

Ao enviar um PR, você concorda que o código é licenciado sob a [AGPL-3.0-or-later](LICENSE) e a documentação sob a [CC BY-SA 4.0](LICENSE-DOCS.md), as mesmas do projeto. O nome e o logotipo "Caderneta" não fazem parte dessas licenças (veja [NOTICE](NOTICE)).

---

## English

Thank you for your interest in Caderneta. Contributions are welcome: fixes, improvements, documentation and translations.

### Before you start

- **Security flaw?** Do not open an issue: follow [SECURITY.md](SECURITY.md).
- **Big idea or change?** Open an issue first, so we can agree on the approach. The [roadmap](https://ettorecsenatore.github.io/caderneta/en/docs/roadmap) shows what is already planned.
- By taking part, you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

### Environment

Follow [Running locally](https://ettorecsenatore.github.io/caderneta/en/docs/tecnico/desenvolvimento): Postgres and Mailpit in Docker, a FastAPI API, a React web app. `python -m app.seed` creates a made-up school with accounts for each role.

### Project rules

- **One topic per PR.** The `main` branch is protected: every PR goes through CI (lint, tests on real Postgres, dependency and license audit, image build) and is merged with *squash*.
- **Tests:** a behavior change comes with a test. API: `cd api && .venv/bin/pytest`. Web: `cd web && npm run typecheck && npm test`.
- **Style:** `ruff check` and `ruff format` for the API (120-character lines); strict TypeScript for the web app.
- **Isolation between schools:** every new table with a school's data needs `escola_id` and a Row-Level Security policy. `test_diario.py` fails a table without RLS.
- **Personal data (LGPD):** a PR that collects a new kind of personal data updates the data map and the gaps in [`.lgpd/`](.lgpd/). Never use real data in tests, screenshots or issues.
- **Documentation in two languages:** every change to the docs (`website/docs/`) also updates the English version (`website/i18n/en/...`). CI fails if they diverge (`scripts/checar-traducao.py`). The app's legal texts and the `.lgpd/` artifacts stay in Portuguese only.
- **Dependencies:** prefer not to add them. If you must, the license has to be AGPL-compatible (`scripts/auditar-licencas.py`), and Actions and Docker images come in pinned by commit and digest (`scripts/checar-fixacao.py`).
- **Migrations:** every migration has a `downgrade()` that undoes everything (`test_migracoes.py` checks it step by step); a published migration does not change, it is fixed with a new one. The PR gets a report with the SQL and the operations that delete data.
- **Versions:** a PR that changes something for users adds its item at the top of [`releases.yaml`](releases.yaml) and bumps the version in `api/pyproject.toml` and `web/package.json` ([Versions and What's new](https://ettorecsenatore.github.io/caderneta/en/docs/tecnico/versoes)).
- **The interface is in Brazilian Portuguese**, in plain language: its users are teachers, families and students.

### License of contributions

By opening a PR, you agree that the code is licensed under [AGPL-3.0-or-later](LICENSE) and the documentation under [CC BY-SA 4.0](LICENSE-DOCS.md), the project's licenses. The "Caderneta" name and logo are not covered by them (see [NOTICE](NOTICE)).
