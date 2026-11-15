---
title: "ADR 0002: Várias escolas"
sidebar_label: "ADR 0002: Multiescola"
---

# ADR 0002: Uma instalação, várias escolas, isoladas no banco

- **Status:** aceita (2026-11-15)
- **Contexto:** o piloto será com uma escola, mas a plataforma deve atender várias sem reinstalar tudo. Vazamento de
  dados entre escolas é o pior risco possível.

## Decisão

- Banco único; toda tabela escolar tem `escola_id`.
- **Row-Level Security** no PostgreSQL: a API define `app.escola_id` e `app.usuario_id` por transação, e as políticas
  só retornam linhas daquela escola. O usuário do banco usado pela API não é dono das tabelas e não ignora RLS.
- Testes automatizados tentam ler dados de outra escola em todos os endpoints.

## Como ficou no M1

- Funções `app_escola()` e `app_usuario()` leem as variáveis da transação; a API as define com `set_config(..., true)`,
  que valem só até o fim da transação.
- Políticas especiais: `usuario` é visível se for o próprio, se tiver perfil ou vínculo na escola ativa, ou se for o
  e-mail em processo de login; `convite` também é visível pelo hash do token em uso; `escola` só pode ser criada pelo
  papel dono (CLI `python -m app.cli criar-escola`).
- A API não pode alterar nem apagar a `auditoria` (só inserir).
- Sem contexto definido, o papel da API não enxerga nenhuma linha (testado em `api/tests/test_isolamento.py`).

## Consequências

- Uma escola grande pode, no futuro, ganhar banco próprio sem mudar o código.
- Migrações precisam sempre criar a política RLS junto com a tabela (checado no CI).
