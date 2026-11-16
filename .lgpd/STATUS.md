# Status LGPD — Caderneta

**Atualizado:** 2026-11-16 · **Cenário:** C, híbrido (código existente do M1 ao M3.3 + funcionalidades novas)

> Este material é **orientação técnica**. Não é parecer jurídico nem certificação de conformidade. A validação final é do M8
> (advogado(a) de proteção de dados + encarregado da escola). Veja [roadmap](../website/docs/roadmap.md).

## Fontes usadas

| Fonte | Uso |
|---|---|
| [goul4rt/lgpd-skills](https://github.com/goul4rt/lgpd-skills) (MIT) | Metodologia: pipeline C do `lgpd-audit`, modelos de mapa de dados, ROPA, RIPD |
| [ctresb/leis](https://github.com/ctresb/leis) | Texto das normas: Lei 13.709/2018 (LGPD), Lei 15.211/2025 (ECA Digital), Decreto 12.880/2026, Lei 12.965/2014 (Marco Civil) |
| [MDS — campanha LGPD](https://www.gov.br/mds/pt-br/acesso-a-informacao/governanca/integridade/campanhas/lgpd) | Referência geral de governança |

Limite de verificação: o repositório `leis` ainda **não traz as resoluções da ANPD** (2/2022, 15/2024, 18/2024, 19/2024, 32/2026).
Elas são citadas como a skill as descreve e **precisam ser conferidas no texto oficial** na revisão jurídica.

## Enquadramento

| Pergunta | Resposta | Situação |
|---|---|---|
| Controladora / operadora | Escola = controladora; quem opera a Caderneta = operadora (contrato de operação de dados) | A formalizar (M8) |
| Agente de pequeno porte (Res. CD/ANPD 2/2022)? | **Avaliação técnica: planejar como NÃO enquadrado nas dispensas.** O porte do negócio pode até caber em ATPP (ME, EPP, startup, sem fins lucrativos), mas a dispensa não vale para quem faz **tratamento de alto risco**, e a Caderneta trata dados sensíveis (saúde) de crianças e adolescentes em escala de escola (art. 4º, segundo a skill). Consequências: encarregado formal, atendimento a titulares e comunicação de incidente em prazos padrão. Quem decide é o(a) advogado(a). Planejar para o caso mais exigente custa pouco e evita refazer | Avaliação registrada em 2026-11-16, **a validar no M8** |
| ECA Digital (Lei 15.211/2025) se aplica? | **Tratar como aplicável.** Art. 1º cobre serviço "de acesso provável" por crianças e adolescentes, e alunos têm conta própria | A confirmar no parecer jurídico |
| Alto risco / RIPD | Sim, preventivo: dados de saúde (sensíveis) e de crianças/adolescentes (Res. 2/2022, art. 4º, segundo a skill) | RIPD no M8 |

## Andamento do pipeline C

- [x] L0 STATUS e enquadramento (este arquivo; ATPP em aberto)
- [x] L2 Mapa de dados preliminar: [data-map.md](./data-map.md)
- [ ] L3 Base legal por atividade e avaliação de melhor interesse (propostas no mapa, **a validar**)
- [ ] L4 Encarregado ou canal ATPP
- [ ] L5 Fornecedores, DPAs e transferências internacionais (hospedagem e e-mail ainda não definidos)
- [ ] L6 Retenção, eliminação e anonimização
- [ ] L7 ECA Digital (aferição de idade, supervisão parental) e consentimento
- [ ] L8 Criptografia e chaves, trilha de auditoria (parte já implementada)
- [ ] L9 Direitos dos titulares (DSAR)
- [ ] L10 Resposta a incidentes
- [ ] L11 ROPA ⏸ · L12 RIPD ⏸ · L13 Política de privacidade ⏸ (checkpoints com revisão humana e jurídica)

Pendências priorizadas: [gaps.md](./gaps.md).

## Regra de manutenção

Todo marco que coletar dado pessoal novo atualiza o `data-map.md` e o `gaps.md` **no mesmo PR**.
