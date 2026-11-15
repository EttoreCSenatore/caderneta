---
title: Cadastro de alunos
---

# Cadastro de alunos

A ficha do aluno é a base de tudo. Ela é criada pela escola (manualmente ou por planilha) e complementada pelos responsáveis.

:::tip Entregue no M1
Cadastro, responsáveis, ficha de saúde e importação por planilha já funcionam.
:::

![Lista de alunos com busca e filtro por turma](/img/screenshots/alunos.png)

![Ficha do aluno: dados](/img/screenshots/aluno-dados.png)

## Dados da ficha

| Grupo | Campos | Quem edita |
|---|---|---|
| **Identificação** | Nome, sobrenome, nome social, data de nascimento, foto (opcional), matrícula/RA | Escola |
| **Documentos** | CPF (opcional), certidão (opcional) | Escola |
| **Família** | Responsáveis vinculados, tipo de vínculo, telefones, e-mail, quem pode buscar | Escola e responsável |
| **Emergência** | Contato de emergência, plano de saúde (opcional) | Escola e responsável |
| **Saúde** | Alergias, medicamentos de uso contínuo, condições (ex.: asma, diabetes), restrições alimentares, laudos e necessidades educacionais específicas | Escola e responsável |
| **Escolar** | Turma atual, situação (ativo, transferido, concluiu), histórico de turmas | Escola |

## Responsáveis

Na aba **Família**, a escola cadastra os responsáveis com o tipo de vínculo e as permissões de cada um (buscar o aluno,
receber avisos, contato de emergência, acesso restrito). Os selos mostram quem já usa o app e quem tem convite pendente.
O próprio responsável pode atualizar o telefone e o e-mail dele.

![Responsáveis do aluno](/img/screenshots/aluno-familia.png)

## Informações de saúde

São **dados sensíveis** pela LGPD. Por isso:

- ficam numa tabela separada, criptografada, e cada leitura é registrada na auditoria;
- professores veem só um **alerta resumido** ("Alergia grave a amendoim: leva adrenalina na mochila") definido pela escola,
  não o laudo completo;
- o responsável é quem informa e atualiza, e a escola confirma.

![Ficha de saúde vista pela escola](/img/screenshots/aluno-saude.png)

No celular, o responsável vê e atualiza a ficha do filho:

<img src="/caderneta/img/screenshots/familia-saude-celular.png" alt="Ficha de saúde no celular do responsável" width="320" />

## Importação por planilha

- Modelo CSV para baixar, com colunas de aluno, responsáveis e turma.
- Pré-visualização antes de gravar: mostra linhas com erro (data inválida, e-mail repetido) sem importar nada pela metade.
- Após importar, a escola dispara os convites aos responsáveis.
- Aceita arquivos do Excel brasileiro (separador `;`, codificação Windows-1252) e datas `dd/mm/aaaa`.
- **Tudo ou nada**: se qualquer linha tiver erro, nada é gravado.

![Pré-visualização com erros por linha](/img/screenshots/importar-erros.png)

## Critérios de pronto (M1) ✅

- [x] Escola cria, edita e arquiva alunos (sem apagar o histórico)
- [x] Importação CSV com pré-visualização e relatório de erros
- [x] Vínculo de vários responsáveis, com flags de busca, avisos e emergência
- [x] Convite por link de uso único que expira em 7 dias
- [x] Informações de saúde criptografadas e com leitura auditada
