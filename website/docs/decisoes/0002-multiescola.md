---
title: "ADR 0002: Várias escolas"
sidebar_label: "ADR 0002: Multiescola"
---

# ADR 0002: Uma instalação, várias escolas, isoladas no banco

- **Status:** proposta (2026-11-15)
- **Contexto:** o piloto será com uma escola, mas a plataforma deve atender várias sem reinstalar tudo. Vazamento de
  dados entre escolas é o pior risco possível.

## Decisão

- Banco único; toda tabela escolar tem `escola_id`.
- **Row-Level Security** no PostgreSQL: a API define `app.escola_id` e `app.usuario_id` por transação, e as políticas
  só retornam linhas daquela escola. O usuário do banco usado pela API não é dono das tabelas e não ignora RLS.
- Testes automatizados tentam ler dados de outra escola em todos os endpoints.

## Consequências

- Uma escola grande pode, no futuro, ganhar banco próprio sem mudar o código.
- Migrações precisam sempre criar a política RLS junto com a tabela (checado no CI).
