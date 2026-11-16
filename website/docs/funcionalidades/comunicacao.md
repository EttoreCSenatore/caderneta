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
- **Horário silencioso**: notificações push fora do horário definido pela escola esperam até a manhã seguinte.

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

Ainda falta no M3: mensagens individuais, anexos, lembrete aos pendentes, push/e-mail e alertas.

## Critérios de pronto (M3)

- [x] Avisos da escola toda e de turma, com agendamento (M3.1)
- [ ] Mensagens individuais em conversa, com anexos
- [x] Confirmação "ciente" e painel de leitura para o remetente (M3.1)
- [x] Autorizações digitais com resposta registrada (M3.2)
- [ ] Notificações push e e-mail com horário silencioso
