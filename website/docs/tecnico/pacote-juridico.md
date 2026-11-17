---
title: Pacote para o advogado
---

# Pacote para revisão jurídica (um por instalação)

A Caderneta é software livre: **cada escola, ou quem a atende, instala a sua**, e cada caso tem a sua realidade jurídica (porte, provedores, país, contrato). Por isso o projeto traz um **gerador do pacote para o advogado**: um documento único, montado com os dados daquela instalação, que a escola ou a operadora entrega ao **seu próprio advogado** para revisar.

## O que o pacote tem

| Parte | O que é |
|---|---|
| **1. Carta** | O que é o projeto, os papéis, o que se pede ao advogado e o que o pacote **não** é |
| **2. Ficha da instalação** | Escola, encarregado, operadora, plantão, provedores e países, prazos configurados, onde ficam as chaves |
| **3. Perguntas** | 14 perguntas objetivas, cada uma com **o que o sistema faz hoje**, a **recomendação padrão** e a **decisão pedida**, com espaço de resposta |
| **4. Contrato de operação** | Pontos mínimos (art. 39) para o advogado redigir |
| **5. Parecer e checklist** | Modelo para registrar o resultado e o passo a passo do instalador depois do parecer |
| **Anexos A a H** | Mapa de dados, política de privacidade e termos **desta instalação**, ROPA, RIPD, testes de legítimo interesse, plano de incidentes, lacunas |

## Como gerar

1. Copie o modelo e preencha os dados da instalação:

   ```bash
   cp .lgpd/pacote/instalacao.exemplo.json instalacao.json
   ```

2. Gere o pacote:

   ```bash
   python3 scripts/gerar-pacote-juridico.py --instalacao instalacao.json --saida pacote-juridico
   ```

3. Abra `pacote-juridico/pacote-juridico.html` no navegador e **imprima em PDF** (ou envie o `.md`). Campos sem dado aparecem em vermelho como **[A PREENCHER: campo]** e o comando lista o que falta.

O `instalacao.json` e a pasta gerada ficam fora do Git (têm dados da escola).

## Textos legais próprios de cada instalação

O advogado pode **reescrever** a política de privacidade e os termos. A instalação passa a usar a versão dele assim:

1. Crie uma pasta com `privacidade.md` e/ou `termos.md`, no mesmo formato dos de `api/app/legal/` (cabeçalho com `versao`, `titulo` e `status`; use `status: vigente` e uma `versao` nova).
2. Aponte `CADERNETA_LEGAL_DIR` para essa pasta (e, para o gerador, o campo `textos_legais_dir` do `instalacao.json`).
3. O que faltar na pasta usa o texto padrão do projeto. Todos confirmam a ciência da versão nova no próximo acesso.

A operadora aparece nos textos pelas variáveis `CADERNETA_OPERADORA_NOME` e `CADERNETA_OPERADORA_CONTATO`.

## Quando refazer

Reenvie o pacote ao advogado **quando entrar recurso novo com dado pessoal**, **mudar de provedor** ou de país, **mudar a operadora** e **a cada 12 meses**. O pacote sempre se monta a partir da versão atual do projeto e do mapa de dados, então não fica velho.

:::note Não é aconselhamento jurídico
O pacote foi preparado pelos desenvolvedores com a metodologia pública do `lgpd-skills` e os textos do `leis`. **Não substitui o parecer.** As resoluções da ANPD citadas precisam ser conferidas no texto oficial.
:::
