---
title: Calendário
---

# Calendário escolar

Um calendário em camadas: a escola define o que vale para todos; o professor acrescenta o que vale para as suas turmas.

## Camadas

| Camada | Quem edita | Quem vê | Exemplos |
|---|---|---|---|
| **Escolar (geral)** | Escola | Todos | Feriados, recessos, início e fim de período, reunião de pais, festa junina |
| **Dias sem aula** | Escola | Todos | Feriado, ponte, conselho de classe, greve, evento externo |
| **Turma** | Professor (suas turmas), coordenação, escola | A turma e seus responsáveis | Prova de Matemática, entrega de trabalho, passeio |

## Funcionalidades

- Ao criar o ano letivo, **feriados nacionais** são sugeridos automaticamente; a escola confirma e adiciona os estaduais e municipais.
- Visões de **mês**, **semana** e **lista** (a lista é a padrão no celular).
- Eventos com cor por tipo: feriado, sem aula, avaliação, evento, prazo.
- **Avaliações** criadas em [Notas e médias](./notas-e-medias.md) com data aparecem sozinhas no calendário da turma.
- Aviso automático aos responsáveis quando a escola cadastra um dia sem aula.
- Exportação **iCal** para assinar no Google Agenda ou no calendário do celular.

## O que já funciona (M4)

Tela **Calendário** para todos os perfis, com visões **Lista** (padrão no celular), **Mês** e **Semana**.

- **Quem vê:** a escola vê tudo; professores veem os eventos da escola e das suas turmas; responsáveis e alunos veem os eventos da escola
  e das turmas dos filhos (vínculo restrito não vê). Equipe e professores podem filtrar por turma.
- **Quem cria:** direção e coordenação criam eventos da escola, de qualquer turma, **feriados** e **dias sem aula**. Professores criam
  evento, avaliação e prazo só nas turmas em que lecionam, e editam ou excluem apenas o que criaram.
- **Avaliações com data** (em [Notas e médias](./notas-e-medias.md)) aparecem sozinhas no calendário da turma, só leitura.
- **Feriados nacionais:** botão **Feriados** (direção/coordenação) lista as datas do ano para confirmar. Os nove feriados nacionais por lei
  vêm marcados: Lei 662/1949 (com a redação da Lei 10.607/2002), Lei 6.802/1980 (12/10) e Lei 14.759/2023 (20/11). Carnaval, Sexta-feira da Paixão
  e Corpus Christi (datas móveis, calculadas a partir da Páscoa) ficam desmarcados, pois a escola decide. Feriados estaduais e municipais são
  cadastrados como evento. Importar de novo não duplica.
- **Dia sem aula e feriado bloqueiam a chamada** nessas datas (nova chamada ou mudança de data), com a mensagem do motivo. Um dia sem aula
  só de uma turma não bloqueia as outras. Aulas já registradas nas datas **não são apagadas**: a equipe recebe a contagem para revisar.
- **Aviso às famílias:** ao cadastrar um dia sem aula, as famílias e os alunos do público são notificados (ver [Comunicação](./comunicacao.md)).
- **Assinatura iCal:** botão **Assinar** gera um link para o Google Agenda ou o calendário do celular. O link é uma credencial: aparece **uma vez**,
  só o hash fica guardado, gerar outro derruba o anterior e dá para desativar. O calendário assinado mostra os eventos com o nome da turma na frente,
  **sem nomes de alunos**.

![Calendário do mês](/img/screenshots/calendario-mes.png)

![Feriados do ano](/img/screenshots/calendario-feriados.png)

![Assinatura iCal](/img/screenshots/calendario-assinar.png)

![Lista no celular](/img/screenshots/calendario-lista-celular.png)

Ficam para depois: eventos com horário, recorrência (ex.: toda segunda) e feriados estaduais e municipais pré-carregados.

## Critérios de pronto (M4)

- [x] Calendário escolar editável pela escola, com feriados nacionais pré-carregados (confirmados pela escola)
- [x] Eventos de turma criados por professores, visíveis só para a turma
- [x] Dias sem aula bloqueiam chamada e notificam famílias
- [x] Visões mês/semana/lista e exportação iCal
