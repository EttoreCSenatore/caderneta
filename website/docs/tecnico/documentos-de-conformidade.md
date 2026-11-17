---
title: Documentos de conformidade (M8.4)
---

# Documentos de conformidade: ROPA, RIPD e incidentes

Estes documentos ficam no repositório, em [`.lgpd/`](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd), versionados junto com o código. São **rascunhos técnicos** feitos com a metodologia da skill `lgpd-audit` e **dependem de revisão do encarregado e de um(a) advogado(a)**; não são parecer jurídico.

| Documento | Para que serve | Onde |
|---|---|---|
| **Mapa de dados** | Que dado, por quê, base legal, quanto tempo (A001 a A019) | [data-map.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/data-map.md) |
| **ROPA** (art. 37) | Registro das operações de tratamento, como controladora (a escola) e operadora | [ROPA.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/ROPA.md) |
| **RIPD** (art. 38) | Riscos para os titulares e medidas, com matriz de probabilidade e impacto e avaliação preliminar do ECA Digital | [RIPD.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/RIPD.md) |
| **Plano de resposta a incidentes** (art. 48) | O que fazer nas primeiras horas, prazos, quem decide e modelos de comunicação | [runbook.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/incidentes/runbook.md) |
| **Registro de incidentes** | Modelo do registro de 5 anos, obrigatório mesmo sem comunicação | [log.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/incidentes/log.md) |
| **Lacunas** | Pendências priorizadas (jurídico e técnicas) | [gaps.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/gaps.md) |

## Como cada instalação usa

- A Caderneta é software livre: **cada escola e cada operadora completa** os nomes (razão social, CNPJ, encarregado, plantão) e mantém o seu ROPA, RIPD e registro de incidentes.
- Todo recurso novo que trate dado pessoal atualiza o mapa de dados, o ROPA e, se mudar o risco, o RIPD, no mesmo PR.

## O que o plano de incidentes já traz

- **Ferramenta de contenção:** `python -m app.cli revogar-sessoes [escola_id]` encerra todas as sessões da instalação ou de uma escola.
- **Para uma pessoa:** *Minha conta → Sair em todos os aparelhos* (também cancela o push).
- **Passo a passo:** abrir e anotar o instante da ciência, conter e preservar evidências, dimensionar (separando crianças e adolescentes), decidir com o jurídico se é notificável, comunicar a ANPD e os titulares em até 3 dias úteis, registrar.
- **Atenção:** como quase todo dado da plataforma é de criança ou adolescente, um incidente com exposição real tende a ser notificável. Quem decide é o encarregado com o jurídico.

## O que ainda falta

Veja `T32` a `T34` em [gaps.md](https://github.com/EttoreCSenatore/caderneta/blob/main/.lgpd/gaps.md): testes de legítimo interesse (LIA) das operações A001, A003, A007, A012 e A017; nomes e telefones de plantão e uma **simulação** de incidente; contrato de operação com cada escola e devolução dos dados no fim dele.

:::note Conferir no texto oficial
As resoluções da ANPD (2/2022, 15/2024 e outras) ainda não estão no repositório `ctresb/leis`. Prazos e itens vêm da descrição da skill e **precisam ser conferidos no texto oficial** na revisão jurídica.
:::
