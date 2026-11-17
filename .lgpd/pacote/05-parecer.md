# 5. Modelo de parecer e checklist do instalador

## 5.1 Identificação

- **Advogado(a) e inscrição na OAB:** ____________________
- **Revisão para:** {{escola_nome}} / {{operadora_nome}}
- **Data:** ____/____/______ · **Versão do pacote revisada:** {{versao_projeto}} ({{data}})

## 5.2 Resultado das perguntas (documento 3)

Para cada pergunta, o(a) advogado(a) marcou "de acordo", "de acordo com ajustes" ou a orientação diferente, no próprio documento 3. Resumo:

- [ ] Todas as perguntas respondidas
- [ ] Respostas que mudam o comportamento do sistema (listar): ______________________________

## 5.3 Textos e documentos

| Documento | Situação | Observações |
|---|---|---|
| Política de privacidade | [ ] aprovada como está  [ ] aprovada com ajustes  [ ] substituída pela versão do advogado | |
| Termos de uso | [ ] aprovados como estão  [ ] aprovados com ajustes  [ ] substituídos pela versão do advogado | |
| ROPA | [ ] aprovado  [ ] ajustes | |
| RIPD | [ ] aprovado  [ ] ajustes | |
| Testes de legítimo interesse | [ ] aprovados  [ ] ajustes | |
| Plano de resposta a incidentes | [ ] aprovado  [ ] ajustes | |
| Contrato de operação | [ ] redigido/adaptado  [ ] não se aplica (a escola hospeda) | |

## 5.4 Riscos aceitos

Riscos residuais **médios** do RIPD que o(a) advogado(a) e a escola aceitam, ou que exigem mudança: R05 (professores sem 2FA), R10 (cadastro de responsáveis), R14 (conta de criança sem consentimento parental registrado), R15 (provedores e transferência internacional), R03 (anexos com dado de saúde) e demais:

______________________________________________________________

## 5.5 Assinatura

____________________________________ · ____/____/______

## 5.6 Checklist do instalador (depois do parecer)

1. [ ] **Textos legais:** colocar a versão aprovada em uma pasta, com `status: vigente` e uma `versao` nova, e apontar `CADERNETA_LEGAL_DIR` para ela (a política e os termos desta instalação passam a ser os aprovados; todos confirmam a ciência no próximo acesso).
2. [ ] **Encarregado:** a direção informa nome e e-mail em *Escola*.
3. [ ] **Operadora:** configurar `CADERNETA_OPERADORA_NOME` e `CADERNETA_OPERADORA_CONTATO`.
4. [ ] **Prazos:** conferir os prazos de desligados na tela *Desligados* e os de retenção do servidor.
5. [ ] **Contrato de operação** assinado (se a operadora não for a escola).
6. [ ] **Plantão:** preencher nome e telefone do Responsável de TI da escola e da operadora no plano de incidentes; fazer a **primeira simulação**.
7. [ ] **Backups:** configurar `backup.sh`, guardar a chave de dados e a senha do backup fora do servidor, e rodar o **teste de restauração** com sucesso.
8. [ ] **Monitoramento e alertas** configurados (disponibilidade, erros, falhas de login, backup atrasado).
9. [ ] **Teste de intrusão** feito, sem pendência crítica ou alta.
10. [ ] **Arquivar** este pacote e o parecer assinados. **Refazer a revisão** quando entrar recurso novo com dado pessoal, mudar provedor ou a cada 12 meses.
