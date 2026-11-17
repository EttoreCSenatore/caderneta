# LIA — Teste de legítimo interesse (rascunho)

> Rascunho técnico, não é parecer jurídico. Modelo: skill `lgpd-legal-basis` (goul4rt/lgpd-skills, MIT); evidência de responsabilização (LGPD art. 6º, X e art. 10, § 3º). ⏸ Revisão do encarregado e do jurídico pendente.

- **Atividade:** A007 · Auditoria e segurança (trilha de ações sensíveis) (ver [mapa de dados](../data-map.md) e [ROPA](../ROPA.md))
- **Controladora:** a escola · **Operadora:** `CADERNETA_OPERADORA_NOME`
- **Versão:** v0.1 · 2026-11-17 · **Próxima revisão:** a cada mudança da operação ou em 6 meses

## 1. Finalidade
- **Interesse:** a escola e a operadora precisam provar **quem fez o quê** em dados sensíveis (leitura de ficha de saúde, correção de notas, supervisão de conversas, exportação de dados) e investigar incidentes (LGPD art. 6º, X, e art. 46).
- **Concreto e atual?** Sim, e é exigência de prestação de contas.
- **Lícita?** Sim.

## 2. Necessidade
- **Dados:** ação, entidade e código do registro, usuário que agiu, **IP**, data, detalhes mínimos. **Não** guarda o conteúdo dos dados lidos.
- **Alternativa:** sem trilha não há como apurar abuso por pessoa de dentro.
- **Descartado:** conteúdo de mensagens e fichas, corpo de requisições, localização.

## 3. Balanceamento
| Dimensão | Análise |
|---|---|
| Relação prévia | Equipe, professores e famílias com conta |
| Legítima expectativa | **Alta**: os termos avisam que o acesso é registrado |
| Impacto | **Baixo**: registro de ações próprias; o aluno aparece só por código |
| Vulnerabilidade | Menores aparecem como alvo da ação, sem conteúdo |
| Origem | Observado no uso |
| Salvaguardas | Só inserção (ninguém apaga); acesso restrito à operadora; sem conteúdo |

**Conclusão:** os direitos do titular não prevalecem.

## 4. Salvaguardas
- [x] Transparência: política (itens 2 e 6) e termos (item 3)
- [ ] **Prazo de guarda** da auditoria e do IP: **a definir no parecer** (T5; o Marco Civil fixa 6 meses para registros de acesso)
- [x] Minimização: sem conteúdo
- [x] Sem uso para outra finalidade

## 5. Alto risco e RIPD

Há **criança e adolescente** entre os titulares (critério específico). O tratamento está coberto pelo [RIPD](../RIPD.md) da plataforma, que o trata como alto risco por precaução.

## 6. Parecer

- [ ] Aprovado o uso do art. 7º, IX com as salvaguardas da seção 4
- [ ] Reprovado: mudar a operação ou a hipótese legal

**Revisado por (encarregado e jurídico):** `{pendente}`
