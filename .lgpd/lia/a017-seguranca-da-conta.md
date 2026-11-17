# LIA — Teste de legítimo interesse (rascunho)

> Rascunho técnico, não é parecer jurídico. Modelo: skill `lgpd-legal-basis` (goul4rt/lgpd-skills, MIT); evidência de responsabilização (LGPD art. 6º, X e art. 10, § 3º). ⏸ Revisão do encarregado e do jurídico pendente.

- **Atividade:** A017 · Segurança da conta (limite de tentativas) (ver [mapa de dados](../data-map.md) e [ROPA](../ROPA.md))
- **Controladora:** a escola · **Operadora:** `CADERNETA_OPERADORA_NOME`
- **Versão:** v0.1 · 2026-11-17 · **Próxima revisão:** a cada mudança da operação ou em 6 meses

## 1. Finalidade
- **Interesse:** impedir **adivinhação de senha, enchente de e-mails de recuperação e rastreio de códigos** por quem tenta abusar do sistema.
- **Concreto e atual?** Sim: são ataques comuns a qualquer página de login.
- **Lícita?** Sim (LGPD art. 46).

## 2. Necessidade
- **Dados:** **hash** do IP ou do e-mail, contagem e janela de tempo. **O IP e o e-mail em si não são guardados** nessa tabela.
- **Alternativa:** sem contador não há como limitar. Contar por conta, sem IP, deixaria um atacante bloquear qualquer pessoa.
- **Descartado:** guardar o IP em claro, histórico de tentativas, localização.

## 3. Balanceamento
| Dimensão | Análise |
|---|---|
| Relação prévia | Qualquer pessoa que tente entrar, com ou sem conta |
| Legítima expectativa | **Alta**: limite de tentativas é padrão esperado |
| Impacto | **Mínimo**: o hash não permite voltar ao IP ou e-mail; o dado some em 2 dias |
| Vulnerabilidade | Inclui menores com conta; o dado não identifica a pessoa |
| Origem | Observado no uso |
| Salvaguardas | Hash irreversível, retenção de 2 dias, sem ligação com o cadastro |

**Conclusão:** os direitos do titular não prevalecem; a medida é mínima e necessária.

## 4. Salvaguardas
- [x] Transparência: política (item 2 e 6)
- [x] Oposição: não cabe (inviabilizaria a segurança), explicado na política
- [x] Retenção de 2 dias, apagada pelo worker
- [x] Pseudonimização (hash)
- [x] Sem perfilamento

## 5. Alto risco e RIPD

Há **criança e adolescente** entre os titulares (critério específico). O tratamento está coberto pelo [RIPD](../RIPD.md) da plataforma, que o trata como alto risco por precaução.

## 6. Parecer

- [ ] Aprovado o uso do art. 7º, IX com as salvaguardas da seção 4
- [ ] Reprovado: mudar a operação ou a hipótese legal

**Revisado por (encarregado e jurídico):** `{pendente}`
