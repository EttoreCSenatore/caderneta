---
title: Como rodar localmente
---

# Como rodar localmente

Requisitos: Docker, Python 3.13+ e Node 24+.

## 1. Banco e e-mail de teste

```bash
cd infra
docker compose up -d        # Postgres em 127.0.0.1:5433 e Mailpit em http://localhost:8025
```

O script `infra/postgres/init/01-roles.sh` cria dois papéis: `caderneta_owner` (dono das tabelas, usado só por
migrações e pelo seed) e `caderneta_app` (usado pela API, sujeito ao Row-Level Security). Os e-mails de convite e de
recuperação de senha aparecem no Mailpit.

## 2. API

```bash
cd api
python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head      # cria as tabelas e as políticas RLS
.venv/bin/python -m app.seed         # escola fictícia de demonstração
.venv/bin/uvicorn app.main:app --reload --port 8000
.venv/bin/pytest                     # testes (usam o banco caderneta_test)
```

Documentação interativa da API em `http://localhost:8000/api/docs` (desligada em produção).

## 3. Web app

```bash
cd web
npm ci
npm run dev       # http://localhost:5173 (repassa /api para a porta 8000)
npm test
npm run build
```

## Contas de demonstração

O seed cria a escola fictícia **Colégio Horizonte (demonstração)** com 136 alunos gerados aleatoriamente. As contas e a
senha de demonstração estão documentadas no topo de `api/app/seed.py`. A direção e a coordenação usam 2FA:
`python -m app.seed --codigo` mostra o código atual. O seed recusa rodar com `CADERNETA_ENV=prod`.

## Criar uma escola de verdade

```bash
.venv/bin/python -m app.cli criar-escola "Nome da Escola" direcao@escola.com.br "Nome da Diretora"
```

Cria a escola e envia o convite do primeiro administrador.

## Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `CADERNETA_DATABASE_URL` | Conexão da API (papel `caderneta_app`) |
| `CADERNETA_OWNER_DATABASE_URL` | Migrações, seed e CLI (papel dono) |
| `CADERNETA_DATA_KEY` | Chave AES-256 em base64 para dados sensíveis (**obrigatória em produção**) |
| `CADERNETA_ENV` | `dev`, `test` ou `prod` |
| `CADERNETA_PUBLIC_URL` | Endereço do web app, usado nos links dos e-mails |
| `CADERNETA_COOKIE_SECURE` | `true` em produção (obrigatório) |
| `CADERNETA_SMTP_*`, `CADERNETA_MAIL_FROM` | Envio de e-mail |

Gerar uma chave: `python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`.
Guarde-a fora do banco e do repositório: sem ela, as fichas de saúde não podem ser lidas.
