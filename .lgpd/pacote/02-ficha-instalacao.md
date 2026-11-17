# 2. Ficha da instalação

Preenchida por quem instala. Os valores vêm do arquivo da instalação (`instalacao.json`); o que estiver como **[A PREENCHER]** precisa ser informado antes de enviar ao advogado.

## Escola (controladora)

| Campo | Valor |
|---|---|
| Nome | {{escola_nome}} |
| CNPJ | {{escola_cnpj}} |
| Cidade / UF | {{escola_cidade_uf}} |
| Etapas de ensino atendidas (define a faixa etária dos alunos) | {{etapas_de_ensino}} |
| Número aproximado de alunos | {{numero_de_alunos}} |
| Encarregado (DPO): nome | {{encarregado_nome}} |
| Encarregado (DPO): e-mail | {{encarregado_email}} |
| Enquadramento como agente de pequeno porte (ATPP)? | {{atpp}} |

## Operadora (quem hospeda e mantém)

| Campo | Valor |
|---|---|
| Nome | {{operadora_nome}} |
| CNPJ ou CPF | {{operadora_documento}} |
| Contato | {{operadora_contato}} |
| A operadora é a própria escola? | {{operadora_e_a_escola}} |
| Responsável de TI da escola (plantão): nome e telefone | {{plantao_ti}} |
| Contrato de operação (art. 39) assinado? Data | {{contrato_operacao}} |

## Provedores e países (suboperadores)

| Serviço | Provedor | País ou região |
|---|---|---|
| Hospedagem e banco de dados | {{hospedagem_provedor}} | {{hospedagem_pais}} |
| Armazenamento de arquivos | {{armazenamento_provedor}} | {{armazenamento_pais}} |
| Envio de e-mail | {{email_provedor}} | {{email_pais}} |
| Cópias de segurança (backup) | {{backup_provedor}} | {{backup_pais}} |
| Notificações do navegador (push) | Serviços dos navegadores (Google, Apple, Mozilla, Microsoft) | EUA e outros |

## Configuração desta instalação

| Campo | Valor |
|---|---|
| Prazo para apagar dados complementares de aluno desligado (dias) | {{prazo_aluno_dias}} |
| Prazo para anonimizar conta de usuário desligado (dias) | {{prazo_usuario_dias}} |
| Aviso antes de apagar (dias) | {{prazo_aviso_dias}} |
| Push e modo offline do professor ligados? | {{push_e_offline}} |
| Antivírus de anexos | ClamAV (obrigatório em produção) |
| Textos legais próprios desta instalação? Versão | {{textos_proprios}} |
| Onde ficam a chave de dados e a senha do backup | {{guarda_das_chaves}} |
