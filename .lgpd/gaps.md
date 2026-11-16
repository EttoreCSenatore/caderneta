# Lacunas e pendências — Caderneta

Prioridade: **P1** antes de qualquer dado real (piloto) · **P2** antes do M8 fechar · **P3** melhoria. Itens "[jurídico]" exigem decisão
de advogado(a) ou do encarregado.

## Técnicas (código)

| # | Pri | Lacuna | Marco sugerido |
|---|---|---|---|
| T1 | P1 | **Direitos dos titulares (art. 18)**: não há exportação nem pedido de correção/eliminação de dados de um titular | M8 (DSAR) |
| T2 | P1 | **Retenção e eliminação**: feita só para `notificacao` (90/180 dias, M3.4). Faltam sessões, auditoria, mensagens, avisos e demais tabelas | M8 |
| T3 | P1 | Texto livre sem proteção específica: justificativa de falta (`frequencia`) e mensagens podem conter dado de saúde. Avaliar aviso na tela, campo estruturado ou cifragem | M8 |
| T4 | P2 | **CPF do aluno** guardado sem cifragem (`aluno.cpf`). Tornar opcional por escola e/ou cifrar | M8 |
| T5 | P2 | IP e user agent em `sessao` e `auditoria`: definir prazo, mascarar ou truncar após o período do Marco Civil (art. 15) | M8 |
| T6 | P2 | Contas de alunos: definir o que o aluno vê e se há mecanismo de supervisão parental (ECA Digital) | M3.4 / M8 |
| T7 | P2 | ~~E-mail de notificação mínimo, horário silencioso e e-mail só para adultos~~ **feito no M3.4**. Falta o push: o endpoint identifica o aparelho, então decidir base legal, consentimento e retenção antes | M3 |
| T8 | P2 | Backups cifrados e teste de restauração; backup também precisa respeitar eliminação | M9 |
| T9 | P3 | Trilha de auditoria com encadeamento de hash (hoje é só append-only por permissão) | M8 |
| T11 | P2 | Link iCal é credencial sem validade: definir expiração (ex.: 1 ano) e aviso para renovar; revisar cabeçalho `Referrer` e log de acesso ao feed | M8 |
| T10 | P3 | Registro de consentimento versionado (ledger), se alguma atividade usar consentimento | M8 |

## Organizacionais e jurídicas

| # | Pri | Pendência |
|---|---|---|
| O1 | P1 | [jurídico] Definir quem é a **operadora** e firmar o contrato de operação de dados com cada escola (art. 39) |
| O2 | P1 | [jurídico] Confirmar o enquadramento. Avaliação técnica: **regime padrão** (alto risco por saúde e menores afasta as dispensas de ATPP); só mudar se o parecer disser o contrário |
| O3 | P1 | Nomear **encarregado** (Res. 18/2024) e publicar o contato (no regime padrão não há dispensa; o canal ATPP só valeria se o parecer enquadrar como baixo risco) |
| O4 | P1 | **ECA Digital tratado como aplicável** (decisão de 2026-11-16). [jurídico] Confirmar e mapear as obrigações do Decreto 12.880/2026 (aferição de idade, supervisão parental) antes do piloto. Novas funções do M3 em diante seguem privacidade por padrão (art. 7º) |
| O5 | P1 | [jurídico] Validar a base legal de cada atividade (A002 a A006), em especial saúde (A004) e adolescentes |
| O6 | P1 | **RIPD** preventivo e **ROPA** consolidado (checkpoints humanos) |
| O7 | P1 | **Política de privacidade** e termos, em linguagem simples, públicos (art. 14, §2º e §6º) |
| O8 | P2 | Escolher hospedagem e provedor de e-mail e classificar o papel de cada um; avaliar transferência internacional |
| O9 | P2 | Plano de resposta a incidentes e registro interno de 5 anos (Res. 15/2024, segundo a skill), com simulação |
| O10 | P2 | Escolher a **licença do código** (o repositório público ainda não tem `LICENSE`) |

## Já atendido

- Isolamento por escola com RLS e testes de isolamento
- Ficha de saúde cifrada (AES-GCM) com leitura auditada
- Senhas com hash, 2FA obrigatório para a equipe, tokens guardados só como hash
- Cookie de sessão HttpOnly, SameSite, Secure em produção, proteção CSRF
- Sem rastreadores de terceiros
- Auditoria só de inserção para ações sensíveis (incluindo supervisão de conversas)
- Vínculo **restrito** de responsável respeitado em avisos, autorizações e mensagens
