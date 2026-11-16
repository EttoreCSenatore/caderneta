---
title: Direitos do titular
---

# Direitos do titular de dados (LGPD, arts. 18 e 19)

Toda pessoa tem direito de saber o que a escola guarda sobre ela, de baixar uma cópia e de pedir correção ou eliminação. A Caderneta oferece isso dentro do app, na página **Meus dados** (também linkada em **Minha conta**).

## O que cada pessoa pode fazer

| Direito | Como é atendido |
|---|---|
| **Confirmação e acesso** (art. 18, I e II) | **Na hora**, sozinho: *Baixar meus dados*. O arquivo traz o conteúdo, a origem, as finalidades, os destinatários e a retenção. Pede a senha de novo e fica registrado na auditoria |
| **Portabilidade** (art. 18, V) | O mesmo arquivo, em JSON (formato estruturado e legível por máquina) |
| **Correção, eliminação, informação, revogação de consentimento** (art. 18, III, IV, VI a IX) | Pedido pelo app, com **protocolo e prazo de 15 dias corridos** (art. 19, II). A direção responde e o titular acompanha |
| **Quem pede pela criança** (art. 18, § 3º) | O **responsável** baixa os dados do filho e faz pedidos sobre ele. Os vínculos de responsável marcados como restritos não têm esse acesso |

## O que vai no arquivo (e o que não vai)

- **Vai:** conta, perfis, vínculos, avisos lidos, autorizações respondidas, mensagens escritas pela própria pessoa, notificações; para o aluno: cadastro (inclusive CPF), matrículas, **notas já publicadas**, frequência, elogios e ocorrências visíveis às famílias, autorizações, históricos emitidos e, **só para o responsável**, a ficha de saúde.
- **Fica de fora, para proteger outras pessoas:** contato de outros responsáveis (só nome e tipo), nome de professores, mensagens de outras pessoas.
- **Fica de fora do arquivo automático:** anotações **pedagógicas e reservadas**. **Decisão do responsável:** elas só são entregues **mediante pedido analisado pela direção**, caso a caso, com resposta fundamentada. O advogado confirma esse procedimento no parecer (gap T19).
- A **conta do próprio aluno** não recebe a ficha de saúde (ela também não a vê no app): o aluno pede à escola.

## Para a direção

A página **Pedidos LGPD** (menu da direção e da coordenação) mostra a fila ordenada pelo prazo: *aberto*, *em análise*, *atendido*, *atendido em parte* ou *não atendido*, com selo de **prazo vencido**. A coordenação acompanha; **só a direção responde** e gera arquivos.

- **Pedido recebido fora do app** (balcão, e-mail, telefone): a direção usa *Registrar pedido recebido fora do app* e informa a **data em que a escola recebeu**; o prazo conta dela. Quem pede não precisa saber chamar de "direito do titular": pedido de "apagar meu cadastro" feito em qualquer canal é protocolado.
- **Gerar arquivo de dados:** a direção baixa o arquivo do titular para entregar a quem pediu. A geração fica registrada.
- **Pedido de cancelamento ou eliminação:** o sistema **não apaga nada sozinho**. O pedido fica **aberto** até um funcionário da direção analisar e responder por conta própria, com texto livre (não há respostas prontas). Assim cada caso considera o que a escola precisa guardar.
- **Responder:** a resposta é obrigatória e explicada. Se não for possível atender (por exemplo, **o histórico escolar precisa ser guardado por lei**, art. 16, I), a resposta diz o porquê. O titular é avisado no app.
- **Eliminação:** a direção executa pelas ferramentas existentes: [Desligados](./desligados.md) (apagar agora, com confirmação) para alunos desligados, e a anonimização de contas para usuários. Enquanto o aluno está matriculado, o histórico fica e o restante pode ser apagado por pedido, conforme o parecer.
- Os pedidos e as respostas são **guardados como prova de atendimento** (prestação de contas, art. 6º, X) por **365 dias depois da resposta**, o mesmo prazo dos demais registros, e depois são apagados pelo worker. Pedido ainda aberto nunca é apagado. A escola pode alterar o prazo na configuração do servidor (`CADERNETA_RETENCAO_PEDIDOS_TITULAR_DIAS`).

## Segurança e privacidade do fluxo

- Baixar dados exige **senha de novo**; tentativas erradas contam para o bloqueio da conta.
- Só dados que a pessoa já podia ver no app, mais o que a lei garante (cadastro, CPF).
- Toda exportação e toda resposta ficam na **auditoria** (sem o conteúdo do arquivo).
- Cada escola só vê os próprios pedidos (isolamento por escola no banco).

:::note Limites
Esta página descreve o fluxo técnico. Prazos e o que pode ser negado são **decisão jurídica**: o parecer do M8 valida o procedimento para anotações internas e confirma que a base legal (contrato com a escola, sem consentimento) vale para todas as atividades, o que dispensa um fluxo de revogação de consentimento.
:::
