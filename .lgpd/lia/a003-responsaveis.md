# LIA — Teste de legítimo interesse (rascunho)

> Rascunho técnico, não é parecer jurídico. Modelo: skill `lgpd-legal-basis` (goul4rt/lgpd-skills, MIT); evidência de responsabilização (LGPD art. 6º, X e art. 10, § 3º). ⏸ Revisão do encarregado e do jurídico pendente.

- **Atividade:** A003 · Vínculo com responsáveis, contatos e convites (ver [mapa de dados](../data-map.md) e [ROPA](../ROPA.md))
- **Controladora:** a escola · **Operadora:** `CADERNETA_OPERADORA_NOME`
- **Versão:** v0.1 · 2026-11-17 · **Próxima revisão:** a cada mudança da operação ou em 6 meses

**Observação:** o **cadastro do responsável que usa o app** decorre do contrato com a escola (art. 7º, V). O legítimo interesse cobre os **contatos de terceiros** indicados pela família (avós, vizinhos, pessoas autorizadas a buscar o aluno) e a segurança do aluno.

## 1. Finalidade
- **Interesse:** a escola precisa **falar com a pessoa certa em uma emergência** e saber **quem pode buscar** o aluno.
- **Concreto e atual?** Sim, é rotina de toda escola e afeta a segurança física da criança.
- **Lícita?** Sim.

## 2. Necessidade
- **Dados:** nome, parentesco, telefone, e-mail, "pode buscar", "emergência", "restrito".
- **Alternativa:** lista em papel na secretaria, o que é menos segura e mais difícil de atualizar ou apagar.
- **Descartado:** CPF e endereço do responsável, documentos, fotos.

## 3. Balanceamento
| Dimensão | Análise |
|---|---|
| Relação prévia | Responsável: contratante. Terceiro indicado: **sem relação direta** com a escola |
| Legítima expectativa | **Alta para o responsável; média para o terceiro**, que foi indicado por quem tem a guarda |
| Impacto | Baixo a moderado: contato errado atrasa uma emergência; contato exposto incomoda |
| Vulnerabilidade | O aluno é criança ou adolescente; **o interesse dele (segurança) é o que justifica o tratamento** |
| Origem | Fornecido pelo responsável |
| Salvaguardas | Vínculo **restrito** (responsável sem acesso, p. ex. por decisão judicial); contato de outros responsáveis não aparece no arquivo de dados de um responsável; apagado no desligamento |

**Conclusão:** prevalece o melhor interesse do aluno. Condição: o responsável **informa as pessoas que indica** (orientação na política e na tela de cadastro).

## 4. Salvaguardas
- [x] Transparência na política (item 2)
- [ ] **Texto de orientação no cadastro** pedindo que o responsável avise quem indica (a fazer)
- [x] Minimização, vínculo restrito, apagado no desligamento (365 dias)
- [x] Sem perfilamento nem uso comercial

## 5. Alto risco e RIPD

Há **criança e adolescente** entre os titulares (critério específico). O tratamento está coberto pelo [RIPD](../RIPD.md) da plataforma, que o trata como alto risco por precaução.

## 6. Parecer

- [ ] Aprovado o uso do art. 7º, IX com as salvaguardas da seção 4
- [ ] Reprovado: mudar a operação ou a hipótese legal

**Revisado por (encarregado e jurídico):** `{pendente}`
