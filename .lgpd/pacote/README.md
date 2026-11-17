# Pacote para revisão jurídica

Modelos usados por `scripts/gerar-pacote-juridico.py` para montar o documento que cada instalação entrega ao seu advogado.

- `01-carta.md`, `02-ficha-instalacao.md`, `03-perguntas.md`, `04-contrato-de-operacao.md`, `05-parecer.md`: partes do pacote. `{{campo}}` é preenchido com os dados da instalação.
- `instalacao.exemplo.json`: modelo dos dados da instalação (copie para `instalacao.json`).

Uso e detalhes: [Pacote para o advogado](../../website/docs/tecnico/pacote-juridico.md).

Ao mudar uma decisão ou um recurso que afete o tratamento de dados, atualize também a pergunta correspondente em `03-perguntas.md`.
