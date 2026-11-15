---
id: intro
title: Visão geral
slug: /intro
---

# Caderneta

**Caderneta** é uma plataforma web leve para escolas. Ela junta num só lugar o que hoje fica espalhado entre
diário de papel, planilhas, grupos de WhatsApp e murais:

- **Notas e médias**: o professor lança as notas e a média sai calculada automaticamente, com a regra da escola.
- **Boletim ao vivo**: alunos e responsáveis acompanham notas, médias e faltas a qualquer momento.
- **Comunicação**: avisos gerais, por turma ou para um aluno, e mensagens para a família com confirmação de leitura.
- **Calendário**: a escola define feriados, eventos e dias sem aula; cada professor adiciona eventos só para as suas turmas.
- **Provas e trabalhos**: o professor envia o arquivo e a escola recebe numa fila de impressão organizada.
- **Ficha e histórico do aluno**: dados pessoais, contatos da família, informações de saúde e anotações que
  acompanham o aluno de um ano para o outro.

:::info Status
**M0 (planejamento)** concluído: visão, perfis, funcionalidades, arquitetura e [roadmap](./roadmap.md).
As telas ainda não existem; cada página de funcionalidade ganha screenshots quando o marco correspondente for entregue.
:::

## Quem usa

| Perfil | O que faz na Caderneta |
|---|---|
| **Escola** (direção e secretaria) | Cadastra turmas, alunos e professores, define o calendário, publica avisos gerais, imprime provas |
| **Coordenação** | Acompanha notas e frequência, aprova provas, registra anotações pedagógicas |
| **Professor** | Lança notas e faltas, envia provas e trabalhos, avisa suas turmas, cria eventos de turma |
| **Responsável** | Vê notas, médias, faltas, avisos e mensagens de cada filho; confirma leitura |
| **Aluno** | Vê suas notas, médias, faltas, calendário e avisos da turma |

Detalhes em [Perfis e permissões](./produto/perfis.md).

## Princípios

1. **Fácil antes de completo.** Cada tela resolve uma tarefa. Lançar as notas de uma turma deve levar menos tempo que na planilha.
2. **Leve.** Funciona em celular simples e 3G. Sem app pesado para baixar: é um site que pode ser instalado na tela inicial.
3. **Privado por padrão.** Os dados são de crianças e adolescentes, alguns de saúde. Cada pessoa vê só o que precisa ver
   ([Segurança e LGPD](./tecnico/seguranca-e-lgpd.md)).
4. **Feito para a escola brasileira.** Bimestres ou trimestres, recuperação, frequência mínima de 75%, feriados nacionais e locais.

## Como esta documentação está organizada

- **Produto**: [visão](./produto/visao.md), [perfis](./produto/perfis.md) e [jornadas](./produto/jornadas.md) de cada usuário.
- **Funcionalidades**: uma página por área, com regras, telas e critérios de pronto.
- **Técnico**: [arquitetura](./tecnico/arquitetura.md), [modelo de dados](./tecnico/modelo-de-dados.md) e
  [segurança e LGPD](./tecnico/seguranca-e-lgpd.md).
- **Decisões (ADRs)**: o porquê das escolhas técnicas.
- **[Roadmap](./roadmap.md)**: os marcos de entrega.
