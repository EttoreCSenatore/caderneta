# Lacunas e pendências — Caderneta

Prioridade: **P1** antes de qualquer dado real (piloto) · **P2** antes do M8 fechar · **P3** melhoria. Itens "[jurídico]" exigem decisão
de advogado(a) ou do encarregado.

## Técnicas (código)

| # | Pri | Lacuna | Marco sugerido |
|---|---|---|---|
| T1 | P1 | ~~Direitos dos titulares (art. 18)~~ **feito no M8.2**: baixar os próprios dados (acesso na hora, portabilidade em JSON), pedidos com protocolo e prazo de 15 dias, fila da direção, registro de pedidos de outros canais. **Decisão do responsável:** pedido de cancelamento fica aberto para a direção analisar e responder em texto livre, sem respostas prontas. Falta o advogado confirmar que a base legal (contrato com a escola) vale para todas as atividades, o que dispensa o fluxo de revogação de consentimento | M8 |
| T2 | P1 | **Retenção e eliminação**: feita para notificações, arquivos, anotações removidas, push e **desligados** (alunos e contas). Faltam sessões, auditoria e IP, avisos e mensagens de alunos ativos | M8 |
| T3 | P1 | Texto livre sem proteção específica: justificativa de falta (`frequencia`) e mensagens podem conter dado de saúde. Avaliar aviso na tela, campo estruturado ou cifragem | M8 |
| T4 | P2 | **CPF do aluno** guardado sem cifragem (`aluno.cpf`). Tornar opcional por escola e/ou cifrar | M8 |
| T5 | P2 | IP e user agent em `sessao` e `auditoria`: definir prazo, mascarar ou truncar após o período do Marco Civil (art. 15) | M8 |
| T6 | P2 | Contas de alunos: definir o que o aluno vê e se há mecanismo de supervisão parental (ECA Digital) | M3.4 / M8 |
| T7 | P2 | ~~Push~~ **feito** (M3.5): vazio, sem aluno, retenção do aparelho. Falta classificar o papel dos serviços de push e a transferência internacional (A014) | M8 |
| T8 | P2 | Backups cifrados e teste de restauração; backup também precisa respeitar eliminação | M9 |
| T9 | P3 | Trilha de auditoria com encadeamento de hash (hoje é só append-only por permissão) | M8 |
| T11 | P2 | Link iCal é credencial sem validade: definir expiração (ex.: 1 ano) e aviso para renovar; revisar cabeçalho `Referrer` e log de acesso ao feed | M8 |
| T12 | P1 | ~~Antivírus nos uploads~~ **feito** (ClamAV, falha fechada, obrigatório em produção). Falta testar contra um `clamd` real no ambiente de produção e manter a base de vírus atualizada | M9 |
| T13 | P2 | ~~Eliminação de arquivos~~ **feita** (365/90/365 dias, global). Falta definir prazos por escola com o jurídico e estender a retenção às demais tabelas (T2) | M8 |
| T14 | P2 | **Chave de dados e backup**: o diretório de arquivos é cifrado com a chave de dados. Documentar a guarda da chave, a rotação e o teste de restauração | M9 |
| T16 | P1 | **Anexos de mensagens podem trazer dado de saúde** (atestado, laudo). Definir a base legal (consentimento do responsável, art. 11, I) e avisar na tela; considerar prazo menor para esses anexos | M8 |
| T17 | P2 | Conversor LibreOffice: rodar em contêiner sem rede e sem privilégios no servidor de produção | M8 |
| T15 | P3 | Orientar professores a **não escrever nomes de alunos** em provas adaptadas e no campo de observações | M8 |
| T18 | P1 | **Retenção das anotações mantidas**: a anotação some 30 dias após remover e **com o apagamento do aluno desligado** (T23). Falta definir prazo para o aluno que continua matriculado | M8 |
| T19 | P1 | [jurídico] **Acesso às anotações (art. 18, II)**: o responsável tem direito aos dados do filho, o que inclui anotações pedagógicas e reservadas, hoje invisíveis a ele. **Decisão do responsável (2026-11-17): entregar só mediante pedido analisado pela direção, caso a caso.** O advogado confirma o procedimento (tarjar terceiros, casos de proteção ao menor) | M8 |
| T24 | P2 | O **apagamento de aluno** não alcança backups. Documentar que o backup expira no próprio ciclo e que uma restauração precisa reaplicar o apagamento | M9 |
| T25 | P3 | **Anonimização manual de usuário** não está na API (a conta é de outro titular e o RLS impede). Hoje só o worker faz, com aviso. O fluxo do pedido existe (M8.2); falta o botão de anonimização manual para a direção | M8 |
| T27 | P2 | **2FA para professores**: só a equipe é obrigada. **Decisão do responsável (2026-11-17): manter assim.** Professores veem nomes, notas, anotações e mensagens (de saúde, só o alerta resumido). Reavaliar no parecer e no RIPD | M8 |
| T28 | P3 | Lista de **senhas fracas/vazadas** e **códigos de reserva** do 2FA (recuperação sem depender da direção) | M8 |
| T29 | P2 | ~~Retenção dos pedidos de titulares~~ **feito**: **5 anos depois da resposta** (decisão do responsável: seguir o que a LGPD e a skill `lgpd-dsar` indicam, de 3 a 5 anos; a lei não fixa prazo). Apagados pelo worker; aberto nunca é apagado. O advogado pode reduzir para 3 (`CADERNETA_RETENCAO_PEDIDOS_TITULAR_DIAS`) | M8 |
| T30 | P1 | [jurídico] **Política e termos em rascunho** (`api/app/legal/*.md`, trechos entre colchetes): base legal dos dados de saúde (art. 11), ciência e consentimento específico de um dos pais para **contas de crianças** (art. 14, §1º; **decisão do responsável: a escola pode criar conta de aluno de qualquer idade**), foro, limitação de responsabilidade e níveis de serviço. A **operadora é configurada por instalação** (`CADERNETA_OPERADORA_NOME`). Publicar (`status: vigente`) só após o parecer | M8 |
| T31 | P2 | Completar na política: **lista de provedores** (hospedagem, e-mail, armazenamento, push), país e garantias de **transferência internacional**, prazo de **auditoria/IP** (T5) e de **backups** (T24). Depende de escolher a hospedagem (O8) | M8/M9 |
| T32 | P1 | **Testes de legítimo interesse (LIA)** das operações em art. 7º, IX: A001, A003, A007, A012, A017. Escrever e anexar ao ROPA; o jurídico valida | M8 |
| T33 | P2 | Incidentes: preencher **nomes e telefones de plantão** (escola e operadora) e fazer a **primeira simulação** (4 cenários do runbook); depois, uma por ano | M8/M9 |
| T34 | P2 | **Contrato de operação** com cada escola (O1) deve prever a **devolução e a eliminação dos dados no fim do contrato** e a lista de sub-operadores | M8 |
| T20 | P2 | **Correção e eliminação x versões**: pedido de correção/eliminação precisa apagar também as versões antigas (hoje só a remoção pela autora/equipe). Hoje o pedido é tratado pela direção caso a caso (a eliminação de versões antigas das anotações ainda é manual) | M8 |
| T26 | P2 | **Dados no aparelho do professor (offline, M7.1)**: celular perdido, roubado ou compartilhado. Hoje há cifra + apagamento (sair, troca, 7 dias), mas a cifra não vale com o navegador desbloqueado. Definir com a escola: bloqueio de tela obrigatório, uso de aparelho pessoal (BYOD) x da escola, e procedimento de perda (revogar sessões). Incluir no RIPD (O6) | M8 |
| T21 | P2 | ~~Rota pública de conferência do histórico sem limite~~ **feito** (M8.1): 20 por minuto por IP, e limite de taxa nas demais rotas públicas | M8 |
| T22 | P2 | [jurídico/pedagógico] O PDF é informativo. Confirmar com a rede de ensino o **modelo oficial** do histórico escolar (campos obrigatórios, assinatura, validade) antes de o piloto tratá-lo como documento de transferência | M8 |
| T23 | P1 | ~~Sessão de desligados~~ **feita**. Decisão do responsável: padrão **365 dias** (aluno) e 180 (usuário), configuráveis por escola no software; avaliar prazo menor só para saúde. Falta o parecer jurídico sobre (1) esses prazos e (2) **prazo mínimo de guarda do histórico escolar** da rede de ensino, que define o que o núcleo mantido pode conter e por quanto tempo | M8 |
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
| O10 | P2 | ~~Escolher a licença do código~~ **feito: AGPL-3.0-or-later** (2026-11-16). Licença da documentação e dos screenshots: **CC BY-SA 4.0** (feito). Resta ajustar o titular do copyright |

## Já atendido

- Minimização na virada de ano: professores de anos encerrados deixam de ver os alunos (M6.1)

- Isolamento por escola com RLS e testes de isolamento
- Ficha de saúde cifrada (AES-GCM) com leitura auditada
- Senhas com hash, 2FA obrigatório para a equipe, tokens guardados só como hash
- Cookie de sessão HttpOnly, SameSite, Secure em produção, proteção CSRF
- Sem rastreadores de terceiros
- Auditoria só de inserção para ações sensíveis (incluindo supervisão de conversas)
- Vínculo **restrito** de responsável respeitado em avisos, autorizações e mensagens
