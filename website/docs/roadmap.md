---
id: roadmap
title: Roadmap
---

# Roadmap

O desenvolvimento é dividido em marcos. Cada marco termina com algo **utilizável** e demonstrável, com screenshots
adicionados às páginas de funcionalidade.

| Marco | Objetivo | Status |
|---|---|---|
| **M0: Planejamento** | Visão, perfis, funcionalidades, arquitetura, modelo de dados, segurança, documentação | ✅ Concluído |
| **M1: Fundação** | Monorepo, CI, login e perfis, escola/turmas/disciplinas, cadastro de alunos e responsáveis, importação CSV, convites | ⏳ Próximo |
| **M2: Notas, médias e frequência** | Avaliações, grade de lançamento, motor de médias configurável, boletim, chamada, fechamento de período | Planejado |
| **M3: Comunicação** | Avisos gerais e de turma, mensagens individuais, "ciente", autorizações, push e e-mail | Planejado |
| **M4: Calendário** | Calendário escolar e de turma, feriados nacionais, dias sem aula, iCal | Planejado |
| **M5: Provas e impressão** | Upload, aprovação, fila de impressão com cópias calculadas, trabalhos | Planejado |
| **M6: Histórico e anotações** | Rematrícula em lote, linha do tempo, anotações versionadas, histórico escolar em PDF | Planejado |
| **M7: App de celular** | PWA refinada, offline para notas e chamada, Capacitor nas lojas | Planejado |
| **M8: Piloto** | Deploy de produção, backups, RIPD/LGPD, revisão de segurança, piloto com uma escola | Planejado |

```mermaid
gantt
  dateFormat YYYY-MM-DD
  axisFormat %b/%y
  section Base
  M0 Planejamento        :done, m0, 2026-11-15, 1d
  M1 Fundação            :m1, 2026-11-17, 3w
  section Núcleo
  M2 Notas e frequência  :m2, after m1, 4w
  M3 Comunicação         :m3, after m2, 3w
  M4 Calendário          :m4, after m3, 2w
  section Escola
  M5 Provas e impressão  :m5, after m4, 2w
  M6 Histórico           :m6, after m5, 3w
  section Entrega
  M7 App de celular      :m7, after m6, 3w
  M8 Piloto              :m8, after m7, 4w
```

As datas são estimativas para orientar a ordem; o ritmo real ajusta o gráfico a cada marco.

## M1: Fundação (próximo)

Objetivo: uma escola consegue se cadastrar, montar as turmas e convidar professores e famílias.

- [ ] Monorepo `api/`, `web/`, `infra/`; Docker Compose de desenvolvimento com Postgres e MinIO
- [ ] CI: lint, typecheck, testes, `pip-audit`/`npm audit`, build da documentação
- [ ] Login, sessão segura, 2FA para administradores, recuperação de senha
- [ ] Perfis por escola e troca de perfil no menu
- [ ] RLS por escola com testes de isolamento
- [ ] Ano letivo, períodos, turmas, disciplinas e atribuições de professores
- [ ] Ficha do aluno, vínculos de responsáveis, ficha de saúde criptografada
- [ ] Importação CSV com pré-visualização
- [ ] Convites por link de uso único
- [ ] Dados de demonstração (escola fictícia) para desenvolvimento e screenshots
- [ ] Screenshots nas páginas de [Cadastro de alunos](./funcionalidades/cadastro-de-alunos.md) e [Perfis](./produto/perfis.md)

## Depois do piloto (ideias)

- Grade horária e substituições de professores
- Tarefas de casa com entrega online
- Relatórios para a direção (desempenho por turma, alunos em risco)
- Integração com WhatsApp Business para notificações
- Portal de matrícula para novos alunos
- Versão em inglês e espanhol da interface
