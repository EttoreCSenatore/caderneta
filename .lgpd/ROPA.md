# Registro de Operações de Tratamento (ROPA, LGPD art. 37) — rascunho

> **Rascunho técnico, não é parecer jurídico.** ⏸ Checkpoint: validação do encarregado e do jurídico antes de virar versão publicada. Modelo: skill `lgpd-ropa` (goul4rt/lgpd-skills, MIT).
>
> **Este é o modelo-base da plataforma.** Cada instalação o completa com os dados da escola (razão social, CNPJ, encarregado) e da operadora, e o mantém versionado. Os campos **dados tratados**, **retenção** e **base legal detalhada** de cada operação estão no [mapa de dados](./data-map.md) (mesmos IDs A001 a A019), para não duplicar e divergir.

| Campo | Valor |
|---|---|
| **Controladora** | A escola `{razão social, CNPJ}` |
| **Operadora** | Quem hospeda esta instalação: `CADERNETA_OPERADORA_NOME` (a Caderneta é software livre, não é uma empresa). Se a escola hospeda, acumula os dois papéis |
| **Encarregado (DPO)** | Nome e e-mail informados em *Escola* no app (art. 41) |
| **Enquadramento** | **Regime padrão** (decisão do responsável; ATPP a validar no parecer, Res. CD/ANPD nº 2/2022) |
| **Versão** | v0.1 (rascunho) · 2026-11-17 · **próxima revisão:** a cada novo recurso com dado pessoal e, no mínimo, a cada 6 meses |

## I. Operações como controladora (a escola)

| ID | Operação | Finalidade específica (art. 6º, I) | Hipótese legal (a validar) | Titulares | Agentes externos e papel | Transf. internacional | Medidas de segurança (art. 46) | Alto risco / RIPD |
|---|---|---|---|---|---|---|---|---|
| A001 | Autenticação e sessão | Identificar quem acessa e proteger a conta | 7º, V; 7º, IX (segurança) | Todos, inclusive alunos (inclusive crianças) | Hospedagem (operador) | A definir (O8) | Argon2id, 2FA da equipe, sessão com hash, limite de taxa, TOTP de uso único | Sim, preventivo |
| A002 | Cadastro escolar do aluno | Matrícula e vida escolar | 7º, II e V; art. 14 | Alunos (crianças e adolescentes) | Hospedagem | A definir | RLS por escola, papéis, ano letivo aberto, TLS | **Sim** |
| A003 | Responsáveis e convites | Contato familiar e acesso do responsável | 7º, V e IX | Responsáveis; alunos indiretamente | Hospedagem; e-mail (operador) | A definir | Vínculo restrito, convite de 7 dias com hash | Sim, preventivo |
| A004 | Ficha de saúde | Segurança e cuidado do aluno na escola | **11, I ou 11, II "e": decisão jurídica (T30)** | Alunos (sensível + menor) | Hospedagem | A definir | AES-GCM por aluno, leitura auditada, professor só vê alerta | **Sim (preventivo reforçado)** |
| A005 | Notas, médias e frequência | Avaliação e registro escolar | 7º, II e V | Alunos | Hospedagem | A definir | RLS, período fechado, correção auditada | Sim, preventivo |
| A006 | Comunicação com famílias | Avisos, mensagens e autorizações | 7º, V | Famílias, alunos, equipe | Hospedagem; armazenamento de anexos | A definir | Supervisão auditada, anexos com antivírus e sem EXIF, cifrados | **Sim** (texto livre com dado sensível) |
| A007 | Auditoria e segurança | Prova de quem fez o quê; segurança | 7º, IX; art. 46 | Equipe e famílias | Hospedagem | A definir | Tabela só de inserção; sem conteúdo dos dados | Não |
| A008 | E-mail transacional | Convite e redefinição de senha | 7º, V | Adultos | **Provedor de e-mail (operador)** | A definir | E-mail sem conteúdo, agrupado, só para adultos | Não |
| A009 | Notificações e alertas | Avisar novidades e faltas | 7º, V | Famílias e equipe | E-mail e push | A definir | Sem conteúdo no e-mail/push; horário silencioso | Não |
| A010 | Calendário e iCal | Datas escolares | 7º, V | Escola e turmas | Hospedagem | A definir | Link secreto por hash, revogável, sem nomes de alunos | Não |
| A011 | Provas, anexos e impressão | Preparar e imprimir provas; anexos de mensagens | 7º, V; saúde em anexos: ver A004 | Professores; famílias (anexos) | Armazenamento (operador) | A definir | Cifrado em repouso, antivírus, link assinado de 5 min, retenção automática | Sim (anexos podem ter saúde) |
| A012 | Anotações sobre o aluno | Acompanhamento pedagógico e disciplinar | 7º, V e IX; sensível: decisão jurídica | Alunos | Hospedagem | A definir | Visibilidade por tipo, reservada auditada, versões | **Sim** |
| A013 | Histórico escolar em PDF | Documento de transferência e prova | 7º, II e V | Alunos | Nenhum (PDF gerado no servidor) | Não | Emissão registrada com código; conferência pública só com iniciais | Sim, preventivo |
| A014 | Push no aparelho | Avisar que há novidade | 7º, V | Adultos (alunos excluídos) | **Serviços de push dos navegadores** (papel a classificar) | **Sim** (EUA e outros) | Mensagem vazia, lista de hosts permitidos, retenção do aparelho | Não |
| A015 | Desligados | Eliminar o que perdeu a finalidade | Arts. 15 e 16; 18 | Alunos e usuários desligados | Hospedagem | A definir | Aviso, adiamento, apagar com confirmação, anonimização | Não |
| A016 | Modo offline do professor | Lançar notas e chamada sem internet | 7º, V; art. 6º, III | Alunos das turmas do professor; o professor | Nenhum (fica no aparelho) | Não | Cofre AES-GCM, apagado ao sair e em 7 dias | Sim, preventivo |
| A017 | Segurança da conta | Limitar abuso e proteger acessos | 7º, IX; art. 46 | Quem acessa | Hospedagem | A definir | Só hash do IP/e-mail, apagado em 2 dias | Não |
| A018 | Pedidos de titulares | Atender o art. 18 e provar o atendimento | 7º, II e VI; 6º, X | Quem pede (e menores, via responsável) | Hospedagem | A definir | Só a direção responde; auditoria; exportação com senha | Não |
| A019 | Ciência da política e termos | Provar que a informação foi dada | 7º, VI; 6º, X | Quem acessa | Hospedagem | A definir | Registro por versão | Não |

**Operações em legítimo interesse (art. 7º, IX) que exigem LIA (teste de legítimo interesse):** A001, A003, A007, A012 e A017. As LIAs estão em rascunho, aguardando o parecer: [A001](./lia/a001-autenticacao.md), [A003](./lia/a003-responsaveis.md), [A007](./lia/a007-auditoria.md), [A012](./lia/a012-anotacoes.md) (aprovável **com condições**) e [A017](./lia/a017-seguranca-da-conta.md).

## II. Operações como operadora

### O001 — Operar a plataforma em nome da escola

| Campo | Descrição |
|---|---|
| **Controladoras atendidas** | Cada escola que usa a instalação |
| **Instrumento (art. 39)** | Contrato de operação de dados entre a escola e a operadora: **ainda a escrever** (O1) |
| **Operações sob instrução** | Hospedar, guardar, processar, enviar e-mails e notificações, aplicar a retenção definida pela escola |
| **Dados tratados** | Os de A001 a A019, conforme a escola os cadastra |
| **Sub-operadores** | Hospedagem, e-mail, armazenamento de arquivos: **a escolher** (O8); serviços de push dos navegadores |
| **Isolamento** | Uma escola por vez, com Row-Level Security no banco; testes de isolamento |
| **Devolução e eliminação no fim do contrato** | Exportação pela direção e eliminação **a definir no contrato** (T34) |

## III. Resumo

- **Operações como controladora:** 19 · **como operadora:** 1
- **Em legítimo interesse (precisam de LIA):** 5
- **Com crianças e adolescentes (art. 14 e ECA Digital):** todas as que envolvem alunos, em especial A002, A004, A005, A006, A011, A012 e A013
- **Com RIPD:** um RIPD único da plataforma: [RIPD.md](./RIPD.md)
- **Transferências internacionais:** push dos navegadores (A014) e o que a hospedagem escolhida implicar (O8)
