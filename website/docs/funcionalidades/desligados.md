---
title: Desligados
---

# Alunos e usuários desligados

Dado pessoal que perdeu a finalidade deve ser eliminado (LGPD, arts. 15 e 16). Ao mesmo tempo, a escola precisa **guardar o histórico** de quem passou por ela.
A sessão **Desligados** (direção e coordenação veem; só a direção age) separa as duas coisas: mantém o núcleo histórico e **apaga o resto depois de um prazo, com aviso antes**.

## Quem entra

- **Aluno desligado:** situação transferido, concluiu ou arquivado. A contagem começa no momento em que a situação deixa de ser "ativo"
  (inclusive na rematrícula). Voltar a "ativo" **cancela** a contagem, o adiamento e o aviso.
- **Usuário desligado:** perfil desativado em Equipe (funcionário), ou conta de responsável ou de aluno que ficou sem vínculo depois do apagamento do aluno.

## O que fica e o que sai

| | Fica (histórico) | Sai depois do prazo |
|---|---|---|
| **Aluno** | nome, nascimento, RA, matrículas, **notas**, **frequência** (só o status) e os **históricos emitidos** | ficha de saúde, **anotações e todas as versões**, conversas, mensagens e anexos (arquivos apagados do disco), contatos dos responsáveis, respostas de autorização, CPF e **justificativas de falta** (texto livre, que pode revelar saúde) |
| **Usuário** | o que escreveu continua, atribuído a **"Ex-usuário"** | nome, e-mail, telefone, senha, 2FA, sessões, aparelhos de push, tokens e convites. A conta é **anonimizada** |

O histórico escolar em PDF continua saindo normalmente depois do apagamento, porque usa só o núcleo mantido.

## Prazos e aviso

- **Prazos configuráveis pela direção** (padrão: **365 dias** para dados do aluno, **180 dias** para contas, **aviso 30 dias antes**). O mínimo aceito é 30 dias,
  e o aviso precisa ser menor que os prazos. Confirme com o jurídico o prazo mínimo de guarda do histórico escolar da rede de ensino da sua escola.
- **Aviso antes de apagar:** ao entrar na janela do aviso, a direção recebe uma notificação ("Dados de desligados serão apagados em breve") e as pessoas atingidas recebem
  um **e-mail sem conteúdo**: o responsável do aluno e o usuário desligado. Assim há tempo de pedir uma cópia dos dados. Os responsáveis com vínculo **restrito** não são avisados.
- **Garantia:** o apagamento **só acontece depois de o aviso ter sido dado com a antecedência configurada**. Se o prazo vencer antes do aviso, o apagamento espera.
- **Adiar** (direção): 30, 90, 180 dias ou 1 ano a partir de hoje. Adiar **reinicia o aviso**. Cada adiamento fica na auditoria.
- **Apagar agora** (aluno, direção): para atender a pedido do titular. Exige digitar `APAGAR`, é irreversível e fica na auditoria, só com contagens, sem dados pessoais.

## Detalhes

- Uma conta **só é anonimizada quando todos os perfis dela estão desligados e vencidos**. Quem ainda tem acesso ativo em outra escola mantém a conta, e só o vínculo com
  esta escola fica inativo.
- A auditoria registra `desligados.purgar_aluno`, `desligados.anonimizar_usuario`, `desligados.adiar_*` e `desligados.config`, **sem nomes nem conteúdo**.
- O trabalho roda no worker (`python -m app.cli notificar`), junto com as demais rotinas de retenção.

![Alunos desligados](/img/screenshots/desligados-alunos.png)

![Usuários desligados](/img/screenshots/desligados-usuarios.png)

![Prazos](/img/screenshots/desligados-prazos.png)

## Critérios de pronto

- [x] Área separada de desligados com contagem regressiva
- [x] Aviso antes de apagar (direção e pessoas atingidas) e opção de adiar
- [x] Núcleo histórico mantido e complementares apagados
- [x] Contas anonimizadas, mantendo a autoria como "Ex-usuário"
- [ ] Prazo mínimo de guarda do histórico escolar confirmado pelo jurídico (M8)
