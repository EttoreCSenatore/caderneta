---
title: Histórico e anotações
---

# Histórico do aluno e anotações

O que se sabe sobre o aluno não deve se perder na troca de ano ou de professor.

## Histórico

- Cada **matrícula** liga o aluno a uma turma num ano letivo. Notas, frequência e anotações ficam presas à matrícula,
  então o histórico de anos anteriores continua intacto.
- **Rematrícula em lote** na virada do ano: escolhe a turma de origem, marca aprovados, retidos e transferidos,
  e define a turma de destino.
- Linha do tempo do aluno: turmas, médias finais por ano, frequência, ocorrências.
- **Histórico escolar** em PDF (para transferência), gerado a partir dos dados.

## Anotações

| Tipo | Exemplo | Visível para |
|---|---|---|
| **Pedagógica** | "Melhora muito com atividades em dupla" | Professores do aluno e coordenação |
| **Ocorrência** | Atraso, comportamento, conflito | Coordenação, escola e, se marcado, responsáveis |
| **Elogio** | "Ajudou colegas no projeto de ciências" | Professores, coordenação e responsáveis |
| **Reservada** | Situação familiar delicada | Só coordenação e direção |

- Toda anotação tem autor, data e visibilidade; editar gera nova versão (não apaga a anterior).
- No novo ano, os novos professores veem as anotações pedagógicas dos anos anteriores: o "passar o bastão" entre professores.

## O que já funciona (M6.1: virada de ano e linha do tempo)

Tela **Virada de ano** (direção e coordenação) e aba **Histórico** na ficha do aluno.

- **Novo ano nasce planejado:** o primeiro ano da escola já nasce aberto; os seguintes ficam fechados ("planejados") até a virada, para não
  trocar o ano atual no meio do ano. Só existe um ano aberto por vez.
- **1. Turmas do novo ano** (direção): cria as turmas com a série seguinte (7º A vira 8º A, 6º ano vira 7º ano) e **copia os professores**.
  Depois do 9º ano não há turma seguinte, e os alunos concluem. Quem repete precisa de uma turma da mesma série, criada em Turmas.
- **2. Rematrícula em lote:** escolha a turma de origem e veja cada aluno com a **sugestão do boletim** (aprovado, retido ou pendente, com o motivo)
  e a turma de destino provável (mesma letra). A equipe decide o resultado de cada aluno: **aprovado, retido, transferido ou concluiu**.
  A operação é **tudo ou nada**: se um aluno estiver inconsistente, nada é gravado. Cada decisão fica na auditoria (`rematricula`).
  - Aprovado e retido ganham a matrícula na turma do novo ano; transferido e concluinte mudam a situação do aluno.
  - **Notas, frequência e anotações do ano anterior ficam presas à matrícula antiga**, então o histórico não se perde.
- **3. Encerrar o ano e abrir o seguinte:** exige todos os períodos fechados (só a direção). O novo ano passa a ser o atual.
- **Privacidade na virada:** só o ano letivo **aberto** dá acesso a alunos e turmas. Depois de encerrado o ano, o professor deixa de ver os alunos
  que não são mais dele, e o novo professor vê os da turma dele. (Responsáveis continuam vendo o histórico dos próprios filhos.)
- **Linha do tempo:** um cartão por ano, com turma, resultado, **médias finais e frequência por disciplina**. A direção e a coordenação veem tudo;
  **família e aluno veem só o que os professores publicaram**; **professores veem apenas turma e resultado**, não as notas de outros professores.

![Virada de ano e rematrícula em lote](/img/screenshots/virada-rematricula.png)

![Linha do tempo do aluno](/img/screenshots/linha-do-tempo.png)

Ainda faltam no M6: anotações versionadas com visibilidade por tipo e o histórico escolar em PDF.

## Critérios de pronto (M6)

- [x] Matrículas por ano letivo e rematrícula em lote
- [x] Linha do tempo (o histórico escolar em PDF vem no M6.3)
- [ ] Anotações com tipos, visibilidade e versionamento
- [ ] Anotações e histórico visíveis aos novos professores no ano seguinte
