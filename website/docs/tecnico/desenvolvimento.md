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
.venv/bin/pytest --cov               # com cobertura: reprova abaixo da meta
```

Documentação interativa da API em `http://localhost:8000/api/docs` (desligada em produção).

## 3. Web app

```bash
cd web
npm ci
npm run dev       # http://localhost:5173 (repassa /api para a porta 8000)
npm test
npm run test:cobertura   # com cobertura: reprova abaixo da meta
npm run build
```

**Cobertura mínima (MO.7).** A CI roda os testes com cobertura e reprova abaixo da meta. API: 93% das linhas de `app/` (medido: 94%), em `api/pyproject.toml`. Web: só a lógica de `src/lib/` (as telas são exercitadas pelos testes de ponta a ponta), com metas de 39% das instruções, 43% dos desvios, 30% das funções e 42% das linhas (o medido), em `web/vite.config.ts`. As metas só sobem: quando novos testes elevarem a cobertura, suba a meta no mesmo PR.

## Screenshots da documentação

Com a API e o web app rodando e o seed aplicado:

```bash
cd web
npm run screenshots          # todos
npm run screenshots -- m2    # só um grupo (m1, m2, m3, m4, m5, m6, desligados...)
```

As imagens vão para `website/static/img/screenshots/`. O script falha se aparecer qualquer erro no console do navegador.

## Testes de ponta a ponta do modo offline

Com a API e o seed rodando e o build servido (`npm run build && npx vite preview`, porta 4173):

```bash
cd web && npm run e2e:offline    # Chromium real, service worker, internet cortada
```

## Contas de demonstração

O seed cria a escola fictícia **Colégio Horizonte (demonstração)** com 136 alunos gerados aleatoriamente. As contas e a
senha de demonstração estão documentadas no topo de `api/app/seed.py`. A direção e a coordenação usam 2FA:
`python -m app.seed --codigo` mostra o código atual. O seed recusa rodar com `CADERNETA_ENV=prod`.

```bash
python -m app.seed --simular   # traz a demonstração até hoje
python -m app.seed --remover   # apaga só a demonstração
```

- **`--simular`:** acrescenta o que falta desde o último seed: aulas e chamadas até hoje no bimestre aberto, as provas do bimestre cujas datas já passaram (com notas) e um aviso da semana (sem e-mail nem push). Pode rodar todo dia pelo cron: rodar de novo não duplica nada. Não roda em produção.
- **`--remover`:** apaga a escola de demonstração e as contas `@demo.caderneta.dev`, e nada mais. Se a escola de demonstração tiver alguma conta de fora desse domínio, ela parece real e o comando recusa sem apagar nada. Em produção exige `--confirmar`.

## Criar uma escola de verdade

```bash
.venv/bin/python -m app.cli criar-escola "Nome da Escola" direcao@escola.com.br "Nome da Diretora"

# worker de notificações (avisos agendados, e-mails, retenção); em produção, rode a cada minuto
.venv/bin/python -m app.cli notificar
```

Cria a escola e envia o convite do primeiro administrador.

Outros comandos úteis (`python -m app.cli ...`): `revogar-sessoes [escola_id]` (resposta a incidente), `rotacionar-chave [--simular]` (rotação da chave de dados), `gerar-vapid` (chaves do push).

## Produção, backups e pacote jurídico

- Implantação: [Implantação](./implantacao.md) (`deploy/`).
- Backups e chaves: [Backups, chaves e logs](./backups-chaves-e-logs.md) (`infra/backup/`).
- Pacote para o advogado: [Pacote para o advogado](./pacote-juridico.md) (`scripts/gerar-pacote-juridico.py`).

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
| `CADERNETA_OPERADORA_NOME`, `CADERNETA_OPERADORA_CONTATO` | Quem opera esta instalação (aparece na política e nos termos) |
| `CADERNETA_LEGAL_DIR` | Pasta com textos legais próprios (`privacidade.md`, `termos.md`) |
| `CADERNETA_DATA_KEYS_ANTIGAS` | Chaves antigas, só para ler durante a rotação |
| `CADERNETA_RATE_LIMIT`, `CADERNETA_TOTP_ANTI_REUSO` | Ligados por padrão; desligados só nos testes que não os exercitam |

Gerar uma chave: `python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`.
Guarde-a fora do banco e do repositório: sem ela, as fichas de saúde não podem ser lidas.

## Armazenamento de arquivos

Provas e trabalhos ficam cifrados em `CADERNETA_STORAGE_DIR` (padrão `./storage`, já no `.gitignore`). Em produção o caminho
precisa ser absoluto, fora do código, com permissão só do usuário da API e **dentro do backup**. Veja a
[ADR 0004](../decisoes/armazenamento-de-arquivos.md). Ajuste o limite com `CADERNETA_MAX_ARQUIVO_BYTES`.

Opcionais em desenvolvimento (em produção o antivírus é obrigatório):

| Variável | Efeito |
|---|---|
| `CADERNETA_ANTIVIRUS=clamav` | verifica cada upload no `clamd` (`docker compose --profile antivirus up -d clamav`, porta 3310) |
| `CADERNETA_CONVERSOR=libreoffice` | converte DOCX em PDF no envio (precisa do `soffice` instalado) |
| `CADERNETA_RETENCAO_PEDIDOS_DIAS`, `..._RASCUNHO_DIAS`, `..._ANEXOS_DIAS` | prazos de eliminação (365, 90, 365) |

## Migrations do banco

Toda mudança no banco é uma migration do Alembic em `api/migrations/versions/` (`alembic revision -m "o que muda"`), numerada em sequência e com `upgrade()` **e** `downgrade()`.

- **Ida e volta:** `api/tests/test_migracoes.py` sobe as migrations uma a uma guardando o esquema de cada versão (tabelas, colunas, índices, restrições, RLS, políticas, funções, tipos, gatilhos e permissões do papel do app), depois desce uma a uma e compara a cada passo. Um `downgrade()` que esquece algo reprova o teste e diz o que sobrou ou sumiu.
- **Relatório no PR:** quando um PR mexe em `api/migrations/`, o workflow *Migrations* comenta no PR o SQL de cada migration nova (modo offline do Alembic, sem banco) e aponta o que merece atenção: apagar tabela ou coluna, apagar linhas, mudar tipo, renomear, exigir valor, retirar permissão, desligar RLS, e migrations já publicadas que foram alteradas. Localmente: `python3 scripts/relatorio-migracoes.py --base origin/main --saida relatorio.md`.
- **Migration publicada não muda:** o `upgrade()` dela já rodou em bancos reais. Corrija com uma migration nova. Só o `downgrade()` pode ser consertado, como foi feito na 0001 (as políticas de RLS agora saem antes das tabelas).
- **SQL sem rodar:** `alembic upgrade 0016:0017 --sql` imprime o SQL de um passo.

## Documentação em dois idiomas

O site de documentação é **bilíngue**: o português fica em `website/docs/` e o **inglês** em `website/i18n/en/docusaurus-plugin-content-docs/current/` (mesmos nomes de arquivo). **Toda mudança de documentação atualiza as duas versões.** O CI roda `python3 scripts/checar-traducao.py`, que reprova se faltar uma página em inglês ou se a estrutura (títulos, blocos de código, imagens) divergir. Para ver o inglês localmente: `cd website && npm run build && npm run serve` (o seletor de idioma fica no topo). Os textos legais do app e os artefatos de `.lgpd/` ficam **só em português**, porque aplicam a lei brasileira.
