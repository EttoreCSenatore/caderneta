# Mapa de Dados Pessoais — Caderneta

**Versão:** v1 · **Status:** Preliminar (bases legais são **propostas a validar**) · **Data:** 2026-11-16
**Escopo do código:** `api/app/models.py` até a migração 0005 (M1 a M3.3)
**Encarregado:** não designado

Todos os dados são da escola-controladora e ficam isolados por escola (RLS no PostgreSQL). Titulares: funcionários,
responsáveis (adultos), **alunos (crianças e adolescentes)**.

## 1. Atividades de tratamento

| ID | Atividade | Dados (tabela) | Sensível / menores | Base legal proposta (a validar) | Retenção proposta |
|---|---|---|---|---|---|
| A001 | Autenticação e sessão | `usuario` (e-mail, nome, telefone, hash de senha, segredo TOTP cifrado, falhas de login), `sessao` (hash do token, **IP, user agent**), `token_senha` | Contas de alunos podem ser menores | Art. 7º, V (execução de contrato) | Conta ativa; sessões expiram em até 30 dias; logs de acesso 6 meses (Marco Civil art. 15) |
| A002 | Cadastro escolar do aluno | `aluno` (nome, sobrenome, nome social, **data de nascimento, CPF**, RA, situação), `matricula`, `turma`, `ano_letivo` | **Menores** | Art. 7º, II (obrigação legal/regulatória escolar) e V; art. 14 (melhor interesse) | Guarda do histórico escolar conforme norma educacional (a definir com jurídico). **Acesso:** só o ano letivo aberto dá acesso a professores (M6.1); a rematrícula é auditada |
| A003 | Vínculo com responsáveis e convites | `vinculo_responsavel` (nome, parentesco, telefone, e-mail, pode buscar, emergência, **restrito**), `convite` (e-mail, nome, papel) | Menores indiretamente | Art. 7º, V e IX (legítimo interesse, segurança do aluno) | Enquanto o vínculo estiver ativo; convites expiram em 7 dias |
| A004 | Ficha de saúde | `ficha_saude` (dados e alerta **cifrados com AES-GCM**) | **Sensível (art. 5º, II e art. 11) + menor** | Provável: art. 11, I (consentimento específico e destacado do responsável) para a ficha; art. 11, II, "e" (proteção da vida/incolumidade) para o alerta de emergência. A alínea "f" (tutela da saúde) vale só para profissionais e serviços de saúde, então **não** serve à escola. **Decisão jurídica** | Enquanto matriculado, depois eliminar (a definir) |
| A005 | Notas, médias e frequência | `avaliacao`, `nota`, `aula`, `frequencia` (**justificativa de falta em texto livre**) | Menor; texto livre pode revelar saúde | Art. 7º, II e V | Parte do histórico escolar |
| A006 | Comunicação com famílias | `aviso` e `aviso_leitura` (quem leu e deu ciente), `conversa`/`mensagem`/`conversa_leitura` (**texto livre**), `autorizacao`/`autorizacao_resposta` (quem respondeu, observação) | Menor; texto livre pode conter dados sensíveis | Art. 7º, V; autorização de passeio é manifestação do responsável | Aviso: ano letivo; mensagens: a definir; autorização: ano letivo |
| A007 | Auditoria e segurança | `auditoria` (ação, entidade, **IP**, detalhes), append-only | Possível | Art. 7º, IX e art. 46 (segurança); art. 37 (registro) | Mínimo 6 meses (Marco Civil); definir prazo |
| A008 | Envio de e-mail transacional e de notificação | Endereço, nome, link de convite/redefinição, via SMTP configurável; e-mail de notificação **sem conteúdo**, agrupado por pessoa | Menor (conta de aluno) | Art. 7º, V | Sem armazenamento próprio além do envio |
| A009 | Notificações e alertas | `notificacao` (título e texto curto, que pode citar o aluno; flag de e-mail), `alerta_falta`, preferências em `usuario` (e-mail ligado/desligado, horário silencioso) | Menor (aluno citado no texto; contas de aluno só recebem no app) | Art. 7º, V | **Lidas: 90 dias; qualquer: 180 dias** (worker `app.cli notificar`) |
| A010 | Calendário e assinatura iCal | `evento` (título, descrição, datas, turma, autor), `calendario_token` (hash do link secreto por perfil) | Menor indiretamente (turma do aluno); **sem nomes de alunos** nos eventos e no iCal | Art. 7º, V | Eventos: ano letivo e histórico escolar (a definir); link iCal: até ser revogado (definir validade máxima) |
| A011 | Provas, trabalhos, anexos e impressão | `arquivo` (nome, tipo, tamanho, hash; conteúdo **cifrado em disco**), `pedido_impressao`, `pedido_comentario`, `mensagem_anexo`; downloads auditados | **Sem dados de alunos** em provas por desenho; **anexos de mensagens podem conter dado de saúde** (atestados, laudos) e fotos, que perdem o EXIF | Art. 7º, V; anexos de saúde: ver A004 e a decisão jurídica sobre base legal | **Eliminação automática:** pedidos 365 dias após a aplicação; rascunhos 90 dias; anexos 365 dias; órfãos no disco após 1 hora (worker) |
| A012 | Anotações sobre o aluno | `anotacao` e `anotacao_versao` (texto livre, tipo, autor, ano, visibilidade; **todas as versões guardadas**) | **Menor; texto livre pode revelar situação familiar, saúde ou conflito entre alunos** (principalmente as reservadas) | Art. 7º, V (acompanhamento pedagógico) e IX; se revelar dado sensível, art. 11 (**decisão jurídica**) | Removida: 30 dias e some com as versões. **Anotação mantida: sem prazo definido (ver T18)** |
| A013 | Histórico escolar em PDF | `historico_emitido` (aluno, quem emitiu, quando, código, hash do conteúdo); o PDF não é guardado | Menor (nome, nascimento, RA, notas e frequência no PDF); **CPF, saúde e anotações ficam de fora** | Art. 7º, II (obrigação legal/regulatória escolar) e V | Registro de emissão: acompanha o histórico do aluno (prazo a definir com o jurídico). **Conferência pública** devolve só escola, data e iniciais |
| A014 | Push no aparelho | `push_inscricao` (usuário, **endereço do serviço de push**, datas); a mensagem de push vai **vazia**, sem chaves do aparelho | Contas de aluno **excluídas**; o endereço identifica o aparelho (de adultos) | Art. 7º, V (execução do serviço contratado com a escola); ativação explícita pela pessoa (decisão do projeto: sem consentimento separado, a validar no M8) | Apaga ao desativar, ao sair do app, quando o serviço de push informa que não existe (404/410), após 90 dias sem uso e com a conta desativada |
| A015 | Desligados: apagamento e anonimização | `aluno` (datas de desligamento, adiamento, aviso, apagamento), `usuario_perfil` (idem), `usuario.anonimizado_em`, prazos por escola | Menor; **apaga** saúde, anotações, mensagens, contatos, CPF e justificativas de falta | Art. 15 e 16 (término do tratamento), art. 18, IV e VI | Padrão: 365 dias (aluno) e 180 dias (conta) após o desligamento, aviso 30 dias antes; núcleo histórico mantido (**prazo a confirmar com o jurídico**) |
| A016 | Modo offline do professor | No navegador do professor (IndexedDB, **cifrado** AES-GCM, chave não exportável): diário das turmas (nomes, notas, médias, faltas, chamadas), **identidade do próprio professor** (nome, e-mail, perfis), lista de turmas, nome da escola e fila de lançamentos pendentes | Menor; **sem** saúde, anotações, mensagens, CPF ou contatos; só aparelhos de professores | Art. 7º, V (execução do serviço contratado com a escola); minimização (art. 6º, III); segurança (art. 46) | Apagado ao sair, trocar de perfil/usuário, ao abrir a entrada sem pendências e após 7 dias sem contato com o servidor; não alcança backups do aparelho |

## 2. Cookies, SDKs e telemetria

| Item | Tipo | Finalidade | Essencial? | Observação |
|---|---|---|---|---|
| `cad_session` | Cookie HttpOnly, SameSite=Lax, Secure em produção | Sessão autenticada | Sim | Único cookie. Sem consentimento necessário |
| Service worker / cache da PWA | Armazenamento local | Funcionamento do app | Sim | Verificar que não guarda respostas da API com dados pessoais (M7) |
| Analytics, pixels, replay de sessão, rastreadores | **Nenhum** | n/a | n/a | Mantenha assim: o ECA Digital e o princípio do melhor interesse desaconselham perfilamento de menores |

## 3. Terceiros e papéis jurídicos

| Terceiro | Papel | País | Situação |
|---|---|---|---|
| Hospedagem/banco de dados | Operador | **A definir** | Sem produção ainda. Preferir região no Brasil. Se fora do país, mecanismo de transferência internacional (art. 33) |
| Provedor de e-mail (SMTP) | Operador | **A definir** | Mailpit só em desenvolvimento |
| Push web (M3.5) | Serviços de push dos navegadores (Google, Apple, Mozilla, Microsoft) | EUA e outros | Recebem só "há novidade" e o endereço do aparelho, **nunca conteúdo**. Classificar o papel (operador ou controlador independente) e a transferência internacional no M8 |
| Provedor de armazenamento de arquivos (M5) | Operador | A definir | Provas e anexos |

## 4. Triagem de alto risco

Preventivo **sim** (RIPD): tratamento de dados de **saúde** e de **crianças e adolescentes** em escala de escola
(critérios geral e específico da Res. CD/ANPD 2/2022, art. 4º, segundo a skill `lgpd-data-mapping`).

## 5. Melhor interesse da criança e do adolescente (LGPD art. 14)

- O consentimento específico de um dos pais (art. 14, §1º) vale para **crianças**. Para adolescentes aplica-se o melhor interesse
  e uma base legal adequada; a escola deve registrar qual base usa para cada atividade.
- Informações sobre dados coletados, uso e exercício de direitos devem ser **públicas** (art. 14, §2º) e em linguagem simples (§6º).
- Não condicionar o uso a dados além do estritamente necessário (art. 14, §4º): hoje o CPF do aluno é opcional no cadastro.
- ECA Digital: privacidade no modelo **mais protetivo por padrão** (art. 7º) e medidas desde a concepção (art. 6º).
