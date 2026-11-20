# Segurança / Security

🇧🇷 Português | [🇺🇸 English](#english)

A Caderneta guarda dados de crianças e adolescentes, inclusive de saúde. Levamos falhas de segurança a sério.

## Como reportar uma falha

**Não abra uma issue pública.** Use o canal privado do GitHub:

1. Abra a aba **[Security](https://github.com/EttoreCSenatore/caderneta/security)** do repositório.
2. Clique em **Report a vulnerability** e descreva a falha: o que é, como reproduzir, o impacto que você vê e a versão (commit) testada.

Só os mantenedores veem o relato. Não envie dados pessoais reais; use a escola de demonstração (`python -m app.seed`).

## O que esperar

| Etapa | Prazo |
|---|---|
| Confirmação de recebimento | até 3 dias úteis |
| Avaliação inicial (é falha? qual a gravidade?) | até 7 dias úteis |
| Correção de falha crítica ou alta | o mais rápido possível, com prioridade sobre o resto do trabalho |

Você recebe notícias pelo próprio relato. Quando a correção sair, publicamos um aviso de segurança (GitHub Security Advisory) e damos crédito a quem reportou, se a pessoa quiser.

## Escopo

**Dentro:** o código deste repositório (API, app web, scripts de implantação e de backup) e a configuração padrão de `deploy/`.

**Fora:** instalações operadas por terceiros (fale com a escola ou com quem instalou), ataques de negação de serviço, engenharia social, falhas que exigem acesso físico ao aparelho desbloqueado, e relatórios de ferramentas automáticas sem uma falha demonstrada.

## Testes de boa-fé

Teste só na sua própria instalação, com dados fictícios. Não acesse, altere nem apague dados de outras pessoas e não teste em instalações de escolas. Quem segue estas regras e reporta pelo canal privado não será alvo de nenhuma ação nossa.

## Versões com correções

Só a versão mais recente da branch `main` recebe correções. Quem opera uma instalação deve atualizar quando sair um aviso de segurança.

## Escolas que usam a Caderneta

Se você é de uma escola e suspeita de um incidente (vazamento, acesso indevido), siga o plano de resposta a incidentes da sua instalação e avise o responsável de TI e o encarregado de dados (DPO) da escola. O plano modelo está em [`.lgpd/incidentes/runbook.md`](.lgpd/incidentes/runbook.md).

---

## English

Caderneta stores data about children and teenagers, including health data. We take security flaws seriously.

### How to report a flaw

**Do not open a public issue.** Use GitHub's private channel:

1. Open the repository's **[Security](https://github.com/EttoreCSenatore/caderneta/security)** tab.
2. Click **Report a vulnerability** and describe the flaw: what it is, how to reproduce it, the impact you see and the version (commit) tested.

Only the maintainers see the report. Do not send real personal data; use the demo school (`python -m app.seed`).

### What to expect

| Step | Time |
|---|---|
| Acknowledgement | within 3 business days |
| Initial assessment (is it a flaw? how severe?) | within 7 business days |
| Fix for a critical or high flaw | as soon as possible, ahead of other work |

You get updates in the report itself. When the fix ships, we publish a GitHub Security Advisory and credit the reporter, if they want.

### Scope

**In:** the code in this repository (API, web app, deployment and backup scripts) and the default configuration in `deploy/`.

**Out:** installations run by third parties (contact the school or whoever installed it), denial of service, social engineering, flaws that need physical access to an unlocked device, and automated-tool reports without a demonstrated flaw.

### Good-faith testing

Test only on your own installation, with made-up data. Do not access, change or delete other people's data and do not test against schools' installations. We will take no action against anyone who follows these rules and reports through the private channel.

### Supported versions

Only the latest `main` branch gets fixes. Operators should update when a security advisory is published.
