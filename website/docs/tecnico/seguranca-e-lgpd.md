---
title: Segurança e LGPD
---

# Segurança e LGPD

A Caderneta guarda dados de **crianças e adolescentes**, incluindo **dados de saúde**. Para a LGPD isso significa:
dados de menores devem ser tratados no seu **melhor interesse** (art. 14) e dados de saúde são **sensíveis** (art. 11).
Segurança é requisito desde o primeiro marco, não etapa final.

:::info Estado da conformidade
O [M8 do roadmap](../roadmap.md) reúne a revisão geral de segurança, licenças e adequação à LGPD. O trabalho de código e documentação está pronto:
[revisão de segurança](./revisao-de-seguranca.md), [direitos do titular](../funcionalidades/direitos-do-titular.md), [privacidade e termos](../funcionalidades/privacidade-e-termos.md),
[ROPA, RIPD e plano de incidentes](./documentos-de-conformidade.md), [backups, chaves e logs](./backups-chaves-e-logs.md) e o [pacote para o advogado](./pacote-juridico.md).
**Falta o parecer jurídico e o teste de intrusão por terceiro**, que são externos. O mapa de dados e as lacunas estão em
[`.lgpd/`](https://github.com/EttoreCSenatore/caderneta/tree/main/.lgpd).
:::

## Papéis na LGPD

- **Controladora**: a escola, que decide por que e como os dados são usados.
- **Operadora**: quem hospeda e mantém a instalação (pode ser a própria escola), seguindo as instruções da escola (contrato de operação de dados).
- **Titulares**: alunos, responsáveis e funcionários.

## O que está implementado

- **Acesso:** Argon2id, bloqueio progressivo, 2FA obrigatório para direção e coordenação com código de uso único, convites de uso único, limite de tentativas por IP, troca de senha e "sair em todos os aparelhos".
- **Sessões e web:** sessões no servidor (só o hash do token), cookie `HttpOnly` + `SameSite=Lax` + `Secure`, proteção CSRF por cabeçalho, cabeçalhos de segurança (CSP, HSTS, `nosniff`...), o service worker nunca guarda respostas da API.
- **Isolamento:** Row-Level Security por escola com papel de banco sem privilégios; testes de isolamento e um teste que percorre todas as rotas e exige login fora da lista pública.
- **Dados sensíveis:** ficha de saúde e segredos do 2FA cifrados com AES-256-GCM (dado associado por registro), com **rotação de chave**; professores veem só o alerta resumido; leituras completas são auditadas.
- **Arquivos:** cifrados em repouso, antivírus no envio (falha fechada), imagens sem EXIF, download por link assinado de 5 minutos ([ADR 0004](../decisoes/armazenamento-de-arquivos.md)).
- **Comunicação mínima:** e-mail e push **sem conteúdo**, só para adultos; horário silencioso.
- **Rastreabilidade:** auditoria só de inserção; logs sem dado pessoal (sem query string nem segredos de URL).
- **Retenção:** notificações, anexos, rascunhos, anotações removidas, aparelhos de push e **desligados** têm prazos e apagamento automático, com aviso antes.
- **Direitos do titular:** baixar os próprios dados na hora, pedidos com prazo de 15 dias e fila da direção.
- **Transparência:** política de privacidade e termos públicos, ciência registrada por versão, encarregado informado no app.
- **Backups:** cifrados, com teste de restauração que confere as chaves.
- **Offline do professor:** cofre cifrado no aparelho, apagado ao sair e em 7 dias sem conexão.

Detalhes do login em [Acesso, convites e 2FA](../funcionalidades/acesso-e-convites.md).

## Medidas por tema

### Acesso

- Autenticação com senha forte, limite de tentativas e bloqueio progressivo.
- **2FA (TOTP) obrigatório** para administradores e coordenação; opcional para os demais (decisão do responsável, a rever no parecer).
- Convites por link de uso único que expira; sem cadastro aberto.
- **Autorização em duas camadas**: a API checa o perfil e o vínculo; o PostgreSQL aplica Row-Level Security por escola,
  então um erro na API não vaza dados de outra escola.

### Dados

- TLS em todo tráfego; HSTS e CSP restritiva.
- Ficha de saúde **cifrada em nível de campo**, com chave fora do banco.
- **Minimização**: CPF e documentos são opcionais; professores veem alertas de saúde resumidos, não laudos.
- Backups diários cifrados, cópia fora do servidor, teste de restauração mensal (scripts em `infra/backup/`).
- Hospedagem preferencialmente no **Brasil** (a escolher).

### Rastreabilidade

- Auditoria só de inserção para: alteração de notas após fechamento, leitura de ficha de saúde e de anotação reservada, download de arquivos, exportações de dados, respostas a pedidos de titulares.

### Direitos dos titulares

- Responsável vê e baixa os dados do filho; pedidos de correção, eliminação e portabilidade pelo app, com prazo.
- Retenção: dados de quem saiu são apagados após o prazo definido pela escola, com aviso antes; o histórico escolar é mantido ([Desligados](../funcionalidades/desligados.md)).

### Desenvolvimento

- Dependências auditadas no CI (`pip-audit`, `npm audit`), auditoria de licenças, SBOM e build das imagens de produção. Dependabot com espera de 7 dias; Actions fixadas pelo commit e imagens pelo digest.
- Testes automatizados de permissão: para cada perfil, o que **não** pode ver.
- Dados fictícios em todos os ambientes que não sejam produção; nunca copiar produção para dev.
- **Falha de segurança:** reporte pelo canal privado do GitHub (aba Security, *Report a vulnerability*), nunca em issue pública. Prazos, escopo e regras de teste de boa-fé no [SECURITY.md](https://github.com/EttoreCSenatore/caderneta/blob/main/SECURITY.md). Como contribuir: [CONTRIBUTING.md](https://github.com/EttoreCSenatore/caderneta/blob/main/CONTRIBUTING.md).
