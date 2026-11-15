# Caderneta

> *Notas, avisos e calendário da escola num só lugar.*

![Página inicial da documentação](docs/screenshots/home.png)

**Caderneta** é uma plataforma web leve para escolas, professores, responsáveis e alunos. O professor lança as notas e a
média é calculada automaticamente; alunos e famílias acompanham notas, faltas, avisos e o calendário pelo navegador ou
pelo celular. A escola organiza turmas, calendário, comunicação e a fila de impressão de provas, e o histórico do aluno
passa de um ano para o outro.

**Status:** M1 (fundação) concluído: login com 2FA, convites, perfis, turmas, alunos, responsáveis, ficha de saúde
criptografada e importação por planilha. Próximo: M2, notas, médias e frequência.
**[Ler a documentação](https://ettorecsenatore.github.io/caderneta/)** · [Roadmap](https://ettorecsenatore.github.io/caderneta/docs/roadmap)

![Painel da direção](website/static/img/screenshots/admin-inicio.png)
![Ficha do aluno: família](website/static/img/screenshots/aluno-familia.png)

<img src="website/static/img/screenshots/familia-inicio-celular.png" alt="Responsável no celular" width="240"> <img src="website/static/img/screenshots/configurar-2fa-celular.png" alt="Configuração do 2FA" width="240"> <img src="website/static/img/screenshots/aluno-inicio-celular-escuro.png" alt="Aluno no celular, tema escuro" width="240">

## Funcionalidades planejadas

- Notas, médias automáticas com regra configurável e boletim ao vivo
- Frequência (chamada) com alertas de limite de faltas
- Avisos gerais, de turma e mensagens individuais com confirmação de leitura
- Calendário escolar e de turma, com feriados e dias sem aula
- Upload de provas e trabalhos com fila de impressão
- Ficha do aluno com dados de saúde protegidos, histórico e anotações entre anos
- PWA instalável e, depois, app nas lojas

## Rodar localmente

```bash
cd infra && docker compose up -d                      # Postgres + Mailpit
cd ../api && python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head && .venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --reload --port 8000
cd ../web && npm ci && npm run dev                    # http://localhost:5173
```

Passo a passo, contas de demonstração e variáveis de ambiente em
[Como rodar localmente](https://ettorecsenatore.github.io/caderneta/docs/tecnico/desenvolvimento).

## Estrutura

```text
caderneta/
├── api/          # FastAPI + SQLAlchemy + Alembic (RLS por escola), testes com Postgres real
├── web/          # React + Vite, PWA instalável
├── infra/        # Docker Compose de desenvolvimento
├── website/      # documentação (Docusaurus, pt-BR)
└── .github/      # CI: API, web e docs; deploy da documentação no GitHub Pages
```

## Segurança

A plataforma lida com dados de menores e de saúde. Veja
[Segurança e LGPD](https://ettorecsenatore.github.io/caderneta/docs/tecnico/seguranca-e-lgpd).
