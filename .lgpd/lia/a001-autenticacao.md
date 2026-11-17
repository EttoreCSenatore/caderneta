# LIA — Teste de legítimo interesse (rascunho)

> Rascunho técnico, não é parecer jurídico. Modelo: skill `lgpd-legal-basis` (goul4rt/lgpd-skills, MIT); evidência de responsabilização (LGPD art. 6º, X e art. 10, § 3º). ⏸ Revisão do encarregado e do jurídico pendente.

- **Atividade:** A001 · Autenticação e sessão (parte de segurança: IP e navegador) (ver [mapa de dados](../data-map.md) e [ROPA](../ROPA.md))
- **Controladora:** a escola · **Operadora:** `CADERNETA_OPERADORA_NOME`
- **Versão:** v0.1 · 2026-11-17 · **Próxima revisão:** a cada mudança da operação ou em 6 meses

**Observação:** a base principal da conta é a execução do contrato com a escola (art. 7º, V). O legítimo interesse cobre só a **parte de segurança**: guardar IP e navegador de cada sessão e registrar tentativas de entrada.

## 1. Finalidade
- **Interesse:** impedir acesso indevido a contas com dados de crianças e de saúde, e permitir que a pessoa reconheça acessos que não foram dela.
- **Concreto e atual?** Sim: tentativas de adivinhar senha e uso de conta alheia são riscos reais de qualquer sistema com login.
- **Lícita?** Sim; é dever de segurança (LGPD art. 46).

## 2. Necessidade
- **Dados:** hash do token da sessão, IP, navegador (user agent), datas, contagem de falhas de login.
- **Alternativa menos intrusiva:** sem IP e navegador não há como mostrar "aparelhos conectados" nem investigar acesso suspeito. O IP não é usado para localizar a pessoa.
- **Descartado por minimização:** localização, impressão digital do navegador, cookies de rastreio.

## 3. Balanceamento
| Dimensão | Análise |
|---|---|
| Relação prévia | Usuário convidado pela escola, com conta ativa |
| Legítima expectativa | **Alta**: é comum que um login registre IP e aparelho para segurança |
| Impacto | **Baixo**: o dado só é visto pela própria pessoa e, em investigação, pela operadora |
| Vulnerabilidade | Inclui contas de alunos (menores): o dado é o mesmo e não vai a terceiros |
| Origem | Observado no uso |
| Salvaguardas | A pessoa vê suas sessões em *Minha conta* e encerra todas; sessão expira em 30 dias |

**Conclusão:** os direitos do titular não prevalecem; a medida é proporcional e esperada.

## 4. Salvaguardas
- [x] Transparência na política de privacidade (itens 2 e 6)
- [x] A pessoa encerra suas sessões; oposição ao registro não é possível sem inviabilizar a segurança, o que a política explica
- [x] Retenção curta: sessão até 30 dias; registros de segurança na auditoria (prazo a definir, T5)
- [x] Sem uso para publicidade ou perfilamento (não existe na plataforma)

## 5. Alto risco e RIPD

Há **criança e adolescente** entre os titulares (critério específico). O tratamento está coberto pelo [RIPD](../RIPD.md) da plataforma, que o trata como alto risco por precaução.

## 6. Parecer

- [ ] Aprovado o uso do art. 7º, IX com as salvaguardas da seção 4
- [ ] Reprovado: mudar a operação ou a hipótese legal

**Revisado por (encarregado e jurídico):** `{pendente}`
