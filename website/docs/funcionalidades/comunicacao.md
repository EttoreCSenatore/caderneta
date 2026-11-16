---
title: Comunicação
---

# Comunicação: avisos e mensagens

Substitui bilhetes na agenda e grupos de WhatsApp por canais com destinatário certo e confirmação de leitura.

## Tipos

| Tipo | Quem envia | Quem recebe | Resposta |
|---|---|---|---|
| **Aviso geral** | Escola, coordenação | Toda a escola, um segmento ou um grupo de turmas | Não (só "ciente") |
| **Aviso de turma** | Professor, coordenação, escola | Alunos e responsáveis de uma turma | Não (só "ciente") |
| **Mensagem individual** | Professor, coordenação, escola | Responsáveis de um aluno (e o aluno, se a escola permitir) | Sim, em conversa |
| **Autorização** | Escola, professor | Responsáveis | Autorizo / Não autorizo |

## Regras

- Avisos podem ser marcados como **importantes**: pedem confirmação "ciente" e aparecem fixados até serem confirmados.
- O remetente vê quem leu e quem ainda não leu; pode reenviar lembrete aos pendentes.
- Mensagens individuais ficam no histórico do aluno; a coordenação pode acompanhar as conversas de professores
  (transparência e proteção para ambos os lados).
- Anexos: PDF e imagens até 10 MB, verificados pelo antivírus antes de guardar.
- Agendamento de envio (ex.: publicar segunda às 7h).
- **Horário silencioso**: e-mails fora do horário definido por cada pessoa esperam até o fim do silêncio (padrão 21h às 7h).

## Notificações

Em ordem de custo: dentro do app → push (PWA) → e-mail. WhatsApp e SMS ficam como integração opcional futura,
porque têm custo por mensagem.

## O que já funciona (M3.1: avisos)

Tela **Avisos** no menu de todos os perfis.

- **Quem envia:** direção e coordenação enviam para a escola toda ou para qualquer turma; professores enviam só
  para as turmas em que lecionam. Responsáveis e alunos apenas leem.
- **Quem recebe:** avisos de turma chegam aos responsáveis e alunos (com conta) dessa turma; avisos da escola chegam a todos.
  Responsáveis com vínculo **restrito** não recebem.
- **Agendamento:** defina "Publicar em"; até lá, só o autor e a equipe veem o aviso, marcado como agendado.
- **Ciente:** o aviso pode pedir "Estou ciente". O leitor vê o selo de não lidos no menu.
- **Painel "Quem leu":** o autor (ou a equipe) vê quem leu, quem deu ciente e quem falta. O primeiro horário é preservado.
- **Arquivar:** tira o aviso da caixa de entrada sem apagar o histórico de leitura.

![Caixa de avisos vista pela direção](/img/screenshots/avisos-equipe.png)

![Painel de leitura](/img/screenshots/aviso-painel.png)

![Aviso no celular da família](/img/screenshots/avisos-familia-celular.png)

## O que já funciona (M3.2: autorizações)

Tela **Autorizações** para equipe, professores e responsáveis.

- **Quem pede:** mesmas regras dos avisos. Direção e coordenação pedem para a escola toda ou uma turma; professores só para as suas turmas.
- **Quem responde:** apenas responsáveis, **por aluno** ("Autorizo" ou "Não autorizo"). Quem tem mais de um filho na escola responde uma vez por filho.
  Vínculos restritos não veem o pedido; a conta do aluno também não responde.
- **Prazo:** definido pelo autor; depois dele a resposta fica travada e o pedido aparece como encerrado. Até lá a família pode mudar de ideia.
- **Registro:** cada resposta (e cada troca) é auditada com quem respondeu e quando.
- **Painel:** o autor vê quem autorizou, quem negou e quem ainda não respondeu, aluno por aluno.

![Pedido de autorização no celular](/img/screenshots/autorizacao-familia-celular.png)

![Painel de respostas](/img/screenshots/autorizacao-painel.png)

## O que já funciona (M3.3: mensagens individuais)

Tela **Mensagens** para equipe, professores e responsáveis. Cada conversa é sobre **um aluno**.

- **Quem inicia:** professor (para alunos das suas turmas), direção e coordenação (qualquer aluno) e o responsável, que escolhe um
  professor da turma do filho.
- **Quem participa:** o profissional da escola envolvido e os responsáveis do aluno sem vínculo restrito. Todos os responsáveis do
  aluno veem a mesma conversa. A conta do aluno não participa.
- **Transparência:** direção e coordenação podem abrir qualquer conversa; cada acesso a conversa de outra pessoa fica na auditoria
  (`conversa.supervisao`). Outros professores não veem.
- **Não lidas:** selo no menu e destaque "nova" na lista; abrir a conversa marca como lida.

![Conversa vista pela direção](/img/screenshots/mensagens-conversa.png)

![Lista de conversas no celular](/img/screenshots/mensagens-lista-celular.png)

## O que já funciona (M3.4: notificações e alertas)

Tela **Notificações** (menu e sino no topo do celular, com contador de novas).

- **No app:** avisos, autorizações, mensagens, nota publicada, alerta de faltas e lembretes geram uma notificação para quem deve vê-la.
  Quem envia não é notificado do que enviou.
- **E-mail mínimo:** o e-mail **nunca leva o conteúdo**: só diz "você tem N novidades" e leva ao app. Sai **um por pessoa**, juntando tudo
  o que acumulou. Contas de **alunos (menores) não recebem e-mail**, só notificação dentro do app (privacidade por padrão, ECA Digital art. 7º).
- **Horário silencioso:** padrão das 21h às 7h no fuso da escola; cada pessoa ajusta em **Preferências** e pode desligar o e-mail.
- **Aviso agendado:** a notificação sai na hora marcada, pelo worker.
- **Lembrar pendentes:** no aviso, "Lembrar pendentes" notifica só quem ainda não leu (ou não deu ciente, se o aviso pede). No máximo
  **um lembrete a cada 24 horas** por aviso, auditado.
- **Nota nova:** ao publicar uma avaliação, a família e o aluno com nota lançada são avisados **uma única vez**, sem o valor da nota no texto.
- **Alertas de faltas:** ao registrar a chamada, quando o aluno chega a **15%** e depois a **20%** de faltas no ano (todas as disciplinas,
  contando faltas justificadas, como no boletim), a família e a coordenação são avisadas. Cada nível dispara uma só vez por matrícula.
- **Retenção:** notificações lidas são apagadas após **90 dias** e qualquer notificação após **180**.

### Worker

O e-mail, os avisos agendados e a retenção rodam por um comando, pensado para o cron a cada minuto:

```bash
.venv/bin/python -m app.cli notificar
```

![Aviso com lembrete aos pendentes](/img/screenshots/aviso-lembrete.png)

![Notificações e preferências](/img/screenshots/notificacoes.png)

![Notificações no celular](/img/screenshots/notificacoes-celular.png)

### Anexos nas mensagens

Nas conversas é possível anexar até **3 arquivos** (PDF, JPG ou PNG, 10 MB cada), por exemplo um atestado.

- Fotos são enviadas **sem EXIF**: localização, data e modelo do aparelho são removidos antes de guardar.
- Todo anexo passa pelo antivírus, fica **cifrado** e é baixado por **link assinado de 5 minutos**, preso ao usuário. Cada download é auditado
  (`mensagem.baixar`), inclusive quando a coordenação supervisiona a conversa.
- Só quem participa da conversa abre o anexo. Após 365 dias o anexo é eliminado e o texto da mensagem permanece.

![Anexo em uma conversa](/img/screenshots/mensagem-anexo.png)

## Push no aparelho (M3.5)

Notificação no celular ou no computador, mesmo com o app fechado. Em **Notificações > Aviso no aparelho (push)** a pessoa toca em **Ativar neste aparelho**.

- **Sem conteúdo:** a mensagem de push vai **vazia**, assinada com VAPID. O aparelho mostra sempre o mesmo aviso ("Você tem novidades. Toque para abrir.") e o app
  abre em Notificações, onde o texto fica atrás do login. **Nada sobre o aluno passa pelo Google, pela Apple ou pela Mozilla**, e o servidor não guarda as chaves
  de criptografia do aparelho (só o endereço do serviço de push).
- **Quem recebe:** responsáveis e equipe. **Contas de alunos (menores) não recebem push**, só as notificações dentro do app, como no e-mail.
- **Ativação:** só quando a pessoa clica (o navegador pede a permissão). A base é a execução do serviço contratado com a escola, sem fluxo de consentimento extra,
  e a pessoa pode desativar quando quiser.
- **Horário silencioso:** vale o mesmo do e-mail (padrão 21h às 7h). Um aparelho recebe **um push** por rodada, mesmo com várias novidades.
  Quem já leu a notificação não é avisado.
- **Retenção do aparelho:** a inscrição é apagada ao **desativar**, ao **sair do app** (vários usuários podem dividir o mesmo navegador), quando o serviço de push diz que o
  aparelho **não existe mais**, após **90 dias sem uso** e quando a **conta é desativada**.
- **Segurança:** o endereço do aparelho só é aceito se for de um serviço de push conhecido (Google, Apple, Mozilla, Microsoft), com HTTPS, o que impede o servidor de ser usado
  para chamar endereços internos. Cada inscrição e cancelamento fica na auditoria.
- **Ativação no servidor:** `python -m app.cli gerar-vapid` gera as chaves, que vão no ambiente (`CADERNETA_VAPID_PRIVATE_KEY` é segredo). Sem chaves, o push fica desligado.
- **iPhone:** só funciona com o app instalado na tela inicial (iOS 16.4 ou mais novo). Para os outros casos o e-mail continua cobrindo.

## Critérios de pronto (M3)

- [x] Avisos da escola toda e de turma, com agendamento (M3.1)
- [x] Mensagens individuais em conversa (M3.3); anexos ficam para o M5, junto com o armazenamento de arquivos
- [x] Confirmação "ciente" e painel de leitura para o remetente (M3.1)
- [x] Autorizações digitais com resposta registrada (M3.2)
- [x] Notificações no app e e-mail com horário silencioso (M3.4); push fica para depois
