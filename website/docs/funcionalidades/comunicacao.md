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
- Anexos: PDF e imagens até 10 MB, verificados antes de liberar o download.
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

Ainda falta no M3: **push (PWA)**, que depende de decisões de privacidade (o endereço de push identifica o aparelho). Anexos dependem do armazenamento de arquivos (M5).

## Critérios de pronto (M3)

- [x] Avisos da escola toda e de turma, com agendamento (M3.1)
- [x] Mensagens individuais em conversa (M3.3); anexos ficam para o M5, junto com o armazenamento de arquivos
- [x] Confirmação "ciente" e painel de leitura para o remetente (M3.1)
- [x] Autorizações digitais com resposta registrada (M3.2)
- [x] Notificações no app e e-mail com horário silencioso (M3.4); push fica para depois
