---
title: Acesso, convites e 2FA
---

# Acesso, convites e verificação em duas etapas

:::tip Entregue no M1
Tudo nesta página já funciona. Os screenshots usam a escola fictícia de demonstração.
:::

Não existe cadastro aberto: **toda conta nasce de um convite** da escola. Isso garante que só entra quem a escola
reconhece como professor, responsável ou aluno.

![Tela de entrada](/img/screenshots/entrar.png)

## Convites

1. A direção convida a equipe em **Equipe → Convidar** (professor, coordenação ou direção/secretaria).
   Responsáveis são convidados pela ficha do aluno (aba **Família**) ou em lote, na [importação por planilha](./cadastro-de-alunos.md#importação-por-planilha).
2. A pessoa recebe um e-mail com um link **de uso único, válido por 7 dias**. A tela também mostra o link para a escola
   copiar e mandar por mensagem, caso o e-mail não chegue.
3. Ao abrir o link, a pessoa confirma o nome e cria a senha (mínimo de 10 caracteres, com letras e números).

![Convite enviado, com link para copiar](/img/screenshots/equipe-convite.png)

<img src="/caderneta/img/screenshots/convite-celular.png" alt="Aceitando um convite no celular" width="320" />

Se o e-mail **já tem conta** (ex.: uma professora que também é mãe de aluno), o convite pede a senha atual e só
**acrescenta o novo perfil** à mesma conta. Ela então escolhe com qual perfil entrar e pode trocar pelo menu.

## Verificação em duas etapas (2FA)

Direção, secretaria e coordenação veem dados de todos os alunos, por isso **precisam** de 2FA. No primeiro acesso, a
Caderneta mostra um QR code para um aplicativo autenticador (Google Authenticator, Microsoft Authenticator, 2FAS…) e só
libera o sistema depois que o primeiro código é confirmado. Nos acessos seguintes, depois da senha, pede o código.

<img src="/caderneta/img/screenshots/configurar-2fa-celular.png" alt="Configuração do 2FA no celular" width="320" />

Professores, responsáveis e alunos podem usar 2FA, mas não são obrigados.

## Proteções do login

| Proteção | Como funciona |
|---|---|
| Senhas | Argon2id; nunca guardadas em texto |
| Tentativas erradas | Após 5 erros, bloqueio progressivo (1, 2, 4… até 60 minutos) |
| E-mail inexistente | Mesma resposta e mesmo tempo de um e-mail existente (não revela quem tem conta) |
| Sessão | Cookie `HttpOnly`, `SameSite=Lax`, expira por inatividade (12 h) e após 30 dias |
| CSRF | A API recusa alterações sem o cabeçalho `X-Caderneta`, que outro site não consegue enviar |
| Esqueci a senha | Link de uso único válido por 1 hora; ao redefinir, todas as sessões abertas são encerradas |
| Auditoria | Login, falhas, ativação de 2FA, convites aceitos e troca de senha ficam registrados |
