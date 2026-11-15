---
title: Notas e médias
---

# Notas e médias

O coração da plataforma. O professor lança notas; a Caderneta calcula médias com a regra da escola e mostra tudo na hora
para alunos e responsáveis.

## Conceitos

- **Ano letivo** dividido em **períodos** (bimestres, trimestres ou semestres, a escola escolhe).
- **Avaliação**: prova, trabalho, participação, simulado. Tem disciplina, turma, período, data, **peso** e nota máxima.
- **Nota**: valor de um aluno numa avaliação. Pode ficar em branco (não fez), ser marcada como **dispensada** ou
  **falta justificada**.
- **Média do período** e **média anual** calculadas automaticamente.
- **Recuperação**: nota que substitui ou compõe a média do período, conforme a regra.

## Regra de cálculo configurável

Cada escola (e, se preciso, cada segmento) define a regra uma vez:

| Opção | Exemplos |
|---|---|
| Tipo de média do período | Aritmética · Ponderada pelos pesos das avaliações |
| Média anual | Média dos períodos · Ponderada (ex.: 1º e 2º bim. peso 2, 3º e 4º peso 3) |
| Recuperação | Substitui se maior · Média entre nota e recuperação · Não existe |
| Arredondamento | Uma casa decimal · Para 0,5 mais próximo · Sem arredondamento |
| Média para aprovação | Ex.: 6,0 |
| Escala | 0 a 10 · 0 a 100 · Conceitos (A, B, C, D) mapeados para faixas |

O cálculo roda no servidor, num módulo puro e testado com casos reais de escolas. A média nunca é digitada à mão.

```text
Exemplo (ponderada, aprovação 6,0, arredondamento 0,5):
Prova 1 = 7,0 (peso 2) · Trabalho = 9,0 (peso 1) · Prova 2 = 5,5 (peso 2)
Média = (7,0×2 + 9,0×1 + 5,5×2) / 5 = 6,8 → arredonda para 7,0 ✅
```

## Lançamento rápido

- Grade estilo planilha: alunos nas linhas, avaliações nas colunas.
- `Enter` desce para o próximo aluno; aceita vírgula ou ponto.
- Salva sozinho; mostra "salvo" por célula. Funciona offline e sincroniza ao voltar a conexão.
- Médias atualizam ao lado enquanto digita.

## Boletim

- **Aluno e responsável** veem por disciplina: avaliações, notas, média do período, média anual, faltas e situação
  (aprovado, em recuperação, abaixo da média).
- Destaque visual quando a média está abaixo da média de aprovação.
- **Publicação controlada**: o professor pode lançar e só **publicar** a avaliação quando terminar, para a família não ver notas pela metade.
- Boletim em **PDF** por período e anual.

## Fechamento do período

- A coordenação **fecha** o período: depois disso, alterar uma nota exige justificativa e fica registrado na auditoria.
- Relatório de pendências: avaliações sem nota, alunos sem média.

## Critérios de pronto (M2)

- [ ] CRUD de avaliações com peso e período
- [ ] Grade de lançamento com teclado, autosave e validação
- [ ] Motor de cálculo configurável com testes cobrindo todas as opções da tabela
- [ ] Boletim do aluno/responsável com destaques e publicação controlada
- [ ] Fechamento de período e alteração com justificativa auditada
- [ ] Boletim em PDF
