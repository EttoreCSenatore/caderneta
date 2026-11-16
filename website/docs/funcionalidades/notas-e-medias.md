---
title: Notas e médias
---

# Notas e médias

:::tip Entregue no M2
Diário de notas, motor de médias configurável, boletim (tela e impressão/PDF), recuperação, publicação controlada e
fechamento de período já funcionam. Os screenshots usam a escola fictícia de demonstração.
:::

O professor lança as notas; a Caderneta calcula as médias com a regra da escola e mostra tudo para alunos e
responsáveis assim que o professor publica. **A média nunca é digitada à mão.**

## Conceitos

- **Ano letivo** dividido em **períodos** (bimestres, trimestres ou semestres).
- **Diário**: uma disciplina numa turma (a atribuição do professor). Cada diário tem avaliações e chamada.
- **Avaliação**: prova, trabalho, participação, simulado ou recuperação, com **peso**, valor máximo e data opcional.
- **Nota**: pode ficar em branco (pendente), ser marcada como **dispensada** (`D`) ou **falta justificada** (`J`,
  o aluno fará segunda chamada). Nenhuma das três entra na conta da média.
- **Recuperação**: avaliação marcada como tal; age conforme a regra da escola e **nunca abaixa a média**.

## Lançamento de notas

O professor abre **Início → Notas** (ou a turma → Professores → Abrir diário). As notas ficam numa grade: alunos nas
linhas, avaliações nas colunas, média ao lado.

![Diário de notas do 3º bimestre](/img/screenshots/diario-notas.png)

- Digite a nota (aceita vírgula ou ponto) e tecle **Enter** para descer ao próximo aluno.
- Cada célula **salva sozinha**: fica verde quando gravou e vermelha se o valor for inválido ou passar do máximo.
- A média do aluno é recalculada na hora; abaixo da média de aprovação aparece em vermelho.

![Nota salva e média recalculada](/img/screenshots/diario-lancamento.png)

![Nova avaliação](/img/screenshots/diario-nova-avaliacao.png)

### Publicação controlada

Avaliações nascem **não publicadas**: o professor lança com calma e clica no selo **Não publicada → Publicada**
quando terminar. Alunos e famílias só veem avaliações publicadas, e a média que eles veem considera só essas.

## Regra de cálculo

Cada escola define a regra uma vez por ano letivo em **Escola → Regra de cálculo da média**:

| Opção | Escolhas |
|---|---|
| Média do período | Ponderada pelos pesos das avaliações · Aritmética |
| Média anual | Todos os períodos iguais · Pesos diferentes por período (ex.: 2, 2, 3, 3) |
| Recuperação | Substitui a média se for maior · Média entre média e recuperação (se aumentar) · Não há |
| Arredondamento | Uma casa decimal · Para o 0,5 mais próximo · Sem arredondamento |
| Escala | 0 a 10, 0 a 100 ou qualquer nota máxima; notas de avaliações com outro valor são convertidas |
| Aprovação | Média mínima e frequência mínima |

![Regra de cálculo da média](/img/screenshots/regra-media.png)

```text
Exemplo (ponderada, aprovação 6,0, arredondamento para 0,5):
Prova 1 = 7,0 (peso 2) · Trabalho = 9,0 (peso 1) · Prova 2 = 5,5 (peso 2)
Média = (7,0×2 + 9,0×1 + 5,5×2) / 5 = 6,8 → arredonda para 7,0 ✅
```

O cálculo fica num módulo puro da API (`api/app/medias.py`), sem acesso a banco, com testes de tabela para cada opção.
Mudar a regra recalcula todas as médias do ano na hora e fica registrado na auditoria.

## Boletim

O boletim é a primeira aba da ficha do aluno. Mostra, por disciplina, a média de cada período (com **R** quando a
recuperação foi aplicada), a média anual, as faltas, a frequência e a situação. Clicando numa disciplina aparecem as
notas de cada avaliação.

![Boletim visto pela escola](/img/screenshots/boletim.png)

No celular, cada disciplina vira um cartão:

<img src="/caderneta/img/screenshots/boletim-celular.png" alt="Boletim no celular do responsável" width="320" />

**Imprimir / salvar PDF** gera uma versão limpa para papel (ou PDF pelo próprio navegador), com cabeçalho da escola,
sem menus e sem cores:

![Versão para impressão](/img/screenshots/boletim-impressao.png)

### Situação

| Situação | Quando |
|---|---|
| Cursando | Ano em andamento e média até aqui na média ou acima |
| Abaixo da média | Ano em andamento e média até aqui abaixo da média de aprovação |
| Aprovado / Reprovado | Só depois que **todos os períodos estão fechados** |
| Reprovado por falta | Ano fechado e frequência abaixo da mínima (75% por padrão, pela LDB) |

## Fechamento do período

Em **Escola**, a coordenação ou a direção **fecha** o período. Antes, o botão **Pendências** mostra, diário por diário,
avaliações sem nota, avaliações não publicadas e diários sem aula registrada.

![Pendências do período](/img/screenshots/pendencias.png)

Com o período fechado, o professor só consulta. A **direção** pode corrigir notas e chamadas em qualquer diário
(**Corrigir este diário**), sempre com uma justificativa: cada alteração vai para a auditoria com o valor antes e depois.
Só a direção reabre um período.

![Diário de período fechado](/img/screenshots/diario-fechado.png)

## Critérios de pronto (M2) ✅

- [x] Avaliações com peso, valor máximo, data e período
- [x] Grade de lançamento com teclado, salvamento automático e validação
- [x] Motor de cálculo configurável com testes cobrindo todas as opções da tabela
- [x] Boletim do aluno e do responsável com destaques e publicação controlada
- [x] Fechamento de período e correção pela direção com justificativa auditada
- [x] Boletim para impressão e PDF (pelo navegador; o PDF gerado no servidor fica para o histórico escolar, no M6)

:::note Fica para depois
- Lançar notas sem internet: no M7, junto com o app de celular.
- Avisar a família quando sai uma nota nova: no M3, com as notificações.
:::
