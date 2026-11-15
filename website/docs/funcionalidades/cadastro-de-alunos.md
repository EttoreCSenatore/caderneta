---
title: Cadastro de alunos
---

# Cadastro de alunos

A ficha do aluno é a base de tudo. Ela é criada pela escola (manualmente ou por planilha) e complementada pelos responsáveis.

## Dados da ficha

| Grupo | Campos | Quem edita |
|---|---|---|
| **Identificação** | Nome, sobrenome, nome social, data de nascimento, foto (opcional), matrícula/RA | Escola |
| **Documentos** | CPF (opcional), certidão (opcional) | Escola |
| **Família** | Responsáveis vinculados, tipo de vínculo, telefones, e-mail, quem pode buscar | Escola e responsável |
| **Emergência** | Contato de emergência, plano de saúde (opcional) | Escola e responsável |
| **Saúde** | Alergias, medicamentos de uso contínuo, condições (ex.: asma, diabetes), restrições alimentares, laudos e necessidades educacionais específicas | Escola e responsável |
| **Escolar** | Turma atual, situação (ativo, transferido, concluiu), histórico de turmas | Escola |

## Informações de saúde

São **dados sensíveis** pela LGPD. Por isso:

- ficam numa tabela separada, criptografada, e cada leitura é registrada na auditoria;
- professores veem só um **alerta resumido** ("Alergia grave a amendoim: leva adrenalina na mochila") definido pela escola,
  não o laudo completo;
- o responsável é quem informa e atualiza, e a escola confirma.

## Importação por planilha

- Modelo CSV para baixar, com colunas de aluno, responsáveis e turma.
- Pré-visualização antes de gravar: mostra linhas com erro (data inválida, e-mail repetido) sem importar nada pela metade.
- Após importar, a escola dispara os convites aos responsáveis.

## Critérios de pronto (M1)

- [ ] Escola cria, edita e arquiva alunos (sem apagar o histórico)
- [ ] Importação CSV com pré-visualização e relatório de erros
- [ ] Vínculo de vários responsáveis, com flags de busca, avisos e emergência
- [ ] Convite por link de uso único que expira em 7 dias
- [ ] Informações de saúde criptografadas e com leitura auditada
