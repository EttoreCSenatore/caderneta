---
title: Plano do piloto
---

# Plano do piloto (M9)

O piloto é o primeiro uso **com dados reais**, numa escola, em escala pequena e com acompanhamento. Este plano vale para qualquer instalação nova; ajuste nomes e datas.

## 1. Porta de entrada: só começa com tudo isto marcado (go / no-go)

**Jurídico e privacidade** (veja o [pacote para o advogado](./tecnico/pacote-juridico.md))
- [ ] Pacote gerado, revisado pelo advogado da escola e/ou da operadora, e **parecer assinado**
- [ ] Textos de privacidade e termos **aprovados** (`status: vigente`) e publicados
- [ ] **Contrato de operação** assinado (se a operadora não é a escola)
- [ ] **Encarregado** nomeado e informado no app; operadora configurada
- [ ] Responsáveis informados do uso da plataforma e, para **crianças**, ciência/consentimento conforme o parecer

**Segurança e operação** (veja [Implantação](./tecnico/implantacao.md) e [Backups, chaves e logs](./tecnico/backups-chaves-e-logs.md))
- [ ] Instalação no ar com **HTTPS**, `smoke.sh` sem falhas
- [ ] **Teste de intrusão** feito, sem pendência crítica ou alta
- [ ] **Backup cifrado** rodando e **teste de restauração** feito com sucesso; chave de dados e senha do backup guardadas fora do servidor
- [ ] **Monitoramento e alertas** ativos (`verificar.sh`) com aviso para o plantão
- [ ] **Plantão** definido (Responsável de TI da escola e da operadora, com telefone) e **simulação de incidente** feita
- [ ] Teste em **aparelhos reais**: Android e iPhone, app instalado, **abrir sem internet**, lançar nota e chamada offline, **push** (precisa de HTTPS e chaves VAPID)

**Pessoas**
- [ ] Direção e professores **treinados**; roteiro de apoio entregue
- [ ] Canal de suporte combinado (quem, onde, em quanto tempo)

## 2. Fases

| Fase | Quem usa | Duração sugerida | O que se faz |
|---|---|---|---|
| 0. Preparação | Equipe técnica e direção | 1 a 2 semanas | Instalar, importar alunos e turmas (primeiro na demonstração), cadastrar equipe, treinar |
| 1. Equipe | Direção, coordenação e professores | 2 semanas | Lançar **notas e chamada**, usar o calendário e as provas. **Famílias ainda não**. Confirmar que o dia a dia funciona |
| 2. Famílias de 1 ou 2 turmas | + responsáveis dessas turmas | 2 a 4 semanas | Convites, avisos, autorizações, mensagens, boletim. Acompanhar dúvidas e pedidos de titulares |
| 3. Escola toda | Todas as turmas | até o fim do período | Ampliar com a rotina já estável |
| 4. Encerramento | Todos | 1 semana | Balanço, decisão (seguir, ajustar ou parar) e relatório |

Avance de fase só com a anterior **sem pendência grave** e com o plantão sem incidente aberto.

## 3. Importação dos dados

1. Importe primeiro uma **cópia fictícia** (mesmo formato) para ensaiar.
2. Use a tela **Importar** (CSV): confira alunos duplicados, turmas e responsáveis.
3. Cadastre só o necessário: **CPF do aluno é opcional**; ficha de saúde só o que a escola precisa.
4. Guarde o arquivo original só o tempo necessário e **apague-o** do computador depois de importar.

## 4. Suporte e gravidade

| Gravidade | Exemplo | Primeira resposta |
|---|---|---|
| **Crítica** | Dado de um aluno aparecendo para quem não deveria; site fora no horário de aula; suspeita de invasão | **Imediata**: acionar o plantão e o [plano de incidentes](./tecnico/documentos-de-conformidade.md) |
| Alta | Não consegue lançar nota ou chamada; e-mails não saem | no mesmo dia |
| Média | Erro de cálculo, tela quebrada em um aparelho | até 2 dias úteis |
| Baixa | Sugestão, texto, melhoria | na revisão semanal |

Registre cada chamado sem dado pessoal do aluno (descreva o problema, **não** cole nome, nota ou mensagem).

## 5. Como saber se deu certo (sem coletar dado pessoal)

- Professores que **lançaram nota e chamada** na plataforma no lugar do papel (contagem).
- **Chamadas e notas** lançadas offline e enviadas sem perda.
- Famílias **convidadas** e que **entraram**.
- **Pedidos de titulares** recebidos e **respondidos no prazo** (meta: 100% em até 15 dias).
- **Incidentes de segurança**: meta zero; qualquer um registrado e tratado.
- Chamados por gravidade e **tempo de resposta**.
- Pesquisa curta de satisfação (anônima) com professores e famílias.

## 6. Plano de recuo

Se algo grave acontecer: **voltar ao processo anterior (papel)** enquanto se corrige. Para parar o acesso: `python -m app.cli revogar-sessoes` e parar o serviço `web`. Os dados ficam preservados; a escola decide, com o encarregado, o que comunicar. **Faça backup antes de qualquer atualização.**

## 7. Encerramento do piloto

- **Relatório** com as métricas acima, o que funcionou, o que não, incidentes e pedidos de titulares.
- **Decisão** da escola: seguir, ajustar ou parar.
- Se parar: **exportar** o que a escola quiser e **eliminar** o restante (inclusive backups no ciclo deles), conforme o contrato; confirmar por escrito.
- **Rever** o pacote jurídico e o RIPD com o que se aprendeu.
