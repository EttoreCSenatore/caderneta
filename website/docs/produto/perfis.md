---
title: Perfis e permissões
---

# Perfis e permissões

Cada pessoa entra com a própria conta e um ou mais **perfis** dentro de uma escola. Um professor pode também ser
responsável por um aluno da mesma escola; nesse caso, ele alterna entre os perfis no menu.

## Perfis

| Perfil | Quem é | Escopo |
|---|---|---|
| **Administrador da escola** | Direção, secretaria | A escola inteira |
| **Coordenação** | Coordenador pedagógico | Os segmentos ou turmas que coordena |
| **Professor** | Docente | As turmas e disciplinas atribuídas a ele no ano letivo |
| **Responsável** | Pai, mãe, tutor legal | Os alunos aos quais está vinculado |
| **Aluno** | Estudante (a partir de uma idade definida pela escola) | Ele mesmo |

## Matriz de permissões

Legenda: ✏️ cria e edita · 👁️ só vê · — sem acesso

| Recurso | Escola | Coordenação | Professor | Responsável | Aluno |
|---|---|---|---|---|---|
| Turmas, disciplinas, ano letivo | ✏️ | 👁️ | 👁️ (suas) | — | — |
| Ficha do aluno (dados e contatos) | ✏️ | 👁️ | 👁️ (seus alunos) | ✏️ (contatos) | 👁️ |
| Informações de saúde | ✏️ | 👁️ | 👁️ alertas essenciais | ✏️ | — |
| Notas e avaliações | 👁️ (pode corrigir com justificativa) | 👁️ | ✏️ (suas turmas) | 👁️ | 👁️ |
| Regra de cálculo da média | ✏️ | 👁️ | 👁️ | — | — |
| Frequência | 👁️ | 👁️ | ✏️ (suas aulas) | 👁️ | 👁️ |
| Avisos gerais da escola | ✏️ | ✏️ | 👁️ | 👁️ | 👁️ |
| Avisos de turma | ✏️ | ✏️ | ✏️ (suas turmas) | 👁️ | 👁️ |
| Mensagem para um aluno/família | ✏️ | ✏️ | ✏️ (seus alunos) | 👁️ e responde | — |
| Calendário escolar | ✏️ | 👁️ | 👁️ | 👁️ | 👁️ |
| Eventos de turma | ✏️ | ✏️ | ✏️ (suas turmas) | 👁️ | 👁️ |
| Provas e trabalhos (arquivos) | 👁️ e imprime | 👁️ e aprova | ✏️ | — | — |
| Anotações sobre o aluno | ✏️ | ✏️ | ✏️ (seus alunos) | 👁️ só as marcadas como visíveis | — |
| Registro de auditoria | 👁️ | — | — | — | — |

:::tip Regra de ouro
O servidor decide o que cada um vê. A interface só esconde botões; quem garante o acesso é o banco de dados, com
regras por escola e por vínculo (ver [Segurança e LGPD](../tecnico/seguranca-e-lgpd.md)).
:::

## Cada perfil tem a sua tela inicial

A família vê os filhos; o aluno vê os próprios dados. A partir do M2 essa tela mostra notas, faltas e avisos.

<div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
  <img src="/caderneta/img/screenshots/familia-inicio-celular.png" alt="Início do responsável no celular" width="280" />
  <img src="/caderneta/img/screenshots/aluno-inicio-celular-escuro.png" alt="Início do aluno no celular, tema escuro" width="280" />
</div>

A tela da direção e a do professor estão em [Escola, turmas e equipe](../funcionalidades/escola-e-turmas.md).

## Contas de alunos

- A escola decide a partir de qual série o aluno tem login próprio (sugestão: 6º ano).
- Alunos menores entram por convite do responsável ou da escola; não há cadastro aberto.
- Para os anos iniciais, o acompanhamento é feito só pela conta do responsável.

## Vínculos de responsáveis

- Um aluno pode ter vários responsáveis; um responsável pode ter vários filhos (inclusive em escolas diferentes no futuro).
- Cada vínculo tem um tipo (mãe, pai, tutor, outro) e flags: **pode buscar o aluno**, **recebe avisos**,
  **é o contato de emergência**.
- A escola pode restringir um responsável (ex.: decisão judicial) sem apagar o histórico.
