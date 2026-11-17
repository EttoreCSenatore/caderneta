---
title: Backups, chaves e logs (M8.5)
---

# Backups, chaves e logs

Operação segura de uma instalação com dados reais. Vale para quem hospeda (a operadora ou a própria escola).

## Chaves de dados

A chave de dados (`CADERNETA_DATA_KEY`, AES-256) cifra a **ficha de saúde**, os **segredos do 2FA** e os **arquivos** (provas e anexos).

- **Guarde fora do servidor**, em cofre de segredos ou em local offline, com cópia separada. **Sem a chave, os dados cifrados não abrem**, nem nos backups.
- **Uma chave por instalação** e por ambiente (nunca reuse a de produção em testes).
- **Rotação** (a cada ano, ou na hora se houver suspeita de vazamento):
  1. gere uma chave nova (base64 de 32 bytes) e ponha em `CADERNETA_DATA_KEY`; a antiga vai para `CADERNETA_DATA_KEYS_ANTIGAS`;
  2. reinicie a API. Ela passa a **ler com as duas** e **gravar com a nova**;
  3. rode `python -m app.cli rotacionar-chave --simular` para ver o que falta e depois `python -m app.cli rotacionar-chave` (pode repetir, é seguro) até não sobrar nada;
  4. só então remova a chave antiga da configuração. **Guarde-a enquanto existirem backups feitos com ela.**
- Os links assinados (5 minutos) usam só a chave atual: ao trocar, os links em aberto expiram.

## Backups cifrados

Scripts em `infra/backup/` (precisam de `pg_dump`, `pg_restore`, `psql` e `gpg`):

- **`backup.sh`** gera um arquivo `caderneta-<data>.tar.gpg` com o **banco** e o **diretório de arquivos**, cifrado com AES-256 por uma **senha de backup** (outra, que não é a chave de dados) e com somas de verificação. Apaga os backups com mais de 35 dias (`RETENCAO_DIAS`).
- **`restore-test.sh`** faz o **teste de restauração**: abre o backup, confere as somas, restaura num banco **temporário**, conta os dados e confere que as **chaves de dados abrem** a saúde, o 2FA e os arquivos, e que **nenhum arquivo falta**. Falha se a senha estiver errada, se o backup estiver corrompido ou se a chave não abrir.
- **Faça o teste de restauração a cada backup novo, ao menos uma vez por mês**, e registre o resultado. Backup que nunca foi restaurado não é backup.
- Guarde o backup **em outro lugar** que o servidor (outra conta ou região) e a senha do backup **separada** dele.

### Retenção e apagamentos (T24)

- O backup **expira sozinho em até 35 dias**: o que a escola apagou (aluno desligado, pedido de eliminação) some dos backups nesse prazo.
- Se for preciso **restaurar de verdade**, o que foi apagado depois do backup **volta**. Depois de restaurar: rode `python -m app.cli notificar` (reaplica a retenção dos desligados e os prazos) e peça à direção para **revisar os pedidos de eliminação** posteriores à data do backup e refazê-los. A política de privacidade diz que os backups expiram no ciclo próprio.

## Logs sem dado pessoal

- A aplicação **não registra** conteúdo de requisições, nomes nem e-mails nos logs.
- O **log de acesso do servidor** guardava a URL inteira. Agora ele **tira a query string** (por exemplo, a busca por nome de aluno) e **troca por marcador** os segredos que viajam na URL (convite, link do calendário, código de conferência do histórico). O **IP** continua, porque é o registro de acesso e a base da investigação de incidentes; o prazo de guarda é decisão do parecer (T5).
- Se um proxy reverso ficar na frente, aplique a mesma regra nele: **não registrar query string nem esses caminhos**.
- Rode a API com `--proxy-headers --forwarded-allow-ips=<IP do proxy>` para o limite de tentativas ver o IP real.

## Monitoramento e alertas

O script `deploy/verificar.sh` (para o cron, a cada 10 minutos) confere: `/api/saude` no ar, **backup atrasado** (`ultimo-backup.txt` velho), **disco cheio**, banco respondendo e **serviço parado**; se algo falhar, avisa o plantão por uma URL de alerta (ntfy, healthchecks.io etc.). Veja [Implantação](./implantacao.md). Ficam por configurar: alerta de erros 5xx e de **muitas falhas de login** (ações `login_falhou` na auditoria). Quem recebe o alerta é o plantão técnico (veja o plano de incidentes).

:::note Limites
Ainda **não verificado em produção**: a hospedagem não foi escolhida. Os scripts foram testados com o banco de desenvolvimento em contêiner.
:::
