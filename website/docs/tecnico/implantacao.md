---
title: Implantação
---

# Implantação em produção

Receita para colocar uma instalação no ar em **uma máquina** (qualquer provedor que rode Docker): banco PostgreSQL, antivírus, API, worker e o site com **HTTPS automático**. Vale para uma escola ou para uma operadora que atende várias (uma instalação por escola é o caminho mais simples de isolar).

:::caution Só com dados reais depois do M8
Para ligar com **dados reais de alunos**, a instalação precisa ter passado pelo [pacote para o advogado](./pacote-juridico.md), pelo parecer e pelo [plano do piloto](../piloto.md). Sem isso, use só dados fictícios (demonstração).
:::

## O que sobe

| Serviço | Para quê |
|---|---|
| `web` (Caddy) | Entrega o app, faz o **HTTPS** (Let's Encrypt) e o proxy da `/api`; envia os cabeçalhos de segurança (CSP, HSTS...); log **sem caminho nem query string** |
| `api` | A API (FastAPI) com o papel restrito do banco (o RLS vale) |
| `worker` | A cada minuto: avisos agendados, e-mails, push, **retenção e apagamento de desligados** |
| `migrate` | Roda as migrações com o papel dono e sai |
| `db` | PostgreSQL 17 |
| `clamav` | Antivírus dos anexos (**obrigatório** em produção) |

Só o `web` publica portas (80 e 443). Banco, API e antivírus ficam na rede interna.

## Passo a passo

1. **Máquina:** Linux com Docker e Docker Compose, com um nome (DNS) apontando para ela e as portas 80 e 443 abertas. Pelo menos 2 GB de memória (o antivírus usa mais de 1 GB).
2. **Código:** clone o repositório e entre em `deploy/`.
3. **Configuração:**

   ```bash
   cp .env.example .env
   sh gerar-segredos.sh                  # imprime senhas do banco e a chave de dados: cole os valores no .env
   ```

   Preencha domínio, e-mail do certificado, **operadora** (nome e contato), e o SMTP do provedor de e-mail. **Guarde uma cópia do `.env` e da chave de dados fora do servidor**: sem a chave, os dados cifrados não abrem, nem nos backups.
4. **Subir:**

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

   A primeira subida baixa a base de vírus do antivírus (alguns minutos); a API só inicia quando ele estiver pronto.
5. **Primeira escola e administrador:**

   ```bash
   docker compose -f docker-compose.prod.yml exec api python -m app.cli criar-escola "Nome da Escola" direcao@escola.com.br "Nome da Direção"
   ```

   O convite chega por e-mail; a direção define a senha e configura o 2FA.
6. **Teste de fumaça:** `sh smoke.sh https://seu-dominio` confere o site, a API, os cabeçalhos de segurança, o CSRF e a política de privacidade pública.
7. **Backups e monitoramento:** copie `cron.exemplo` para o `crontab` e ajuste: **backup cifrado diário**, **teste de restauração mensal** e `verificar.sh` a cada 10 minutos (site fora, backup atrasado, disco cheio, banco ou serviço parado), com aviso para o plantão por `ALERTA_URL` (ntfy, healthchecks.io etc.). Veja [Backups, chaves e logs](./backups-chaves-e-logs.md).
8. **Textos legais da escola:** se o advogado aprovou textos próprios, coloque `privacidade.md` e `termos.md` em `deploy/legal/` e descomente `CADERNETA_LEGAL_DIR=/legal` no `.env`.

## Atualizar

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
sh smoke.sh https://seu-dominio
```

O que mudou em cada versão está no [`releases.yaml`](https://github.com/EttoreCSenatore/caderneta/blob/main/releases.yaml) e nas [releases do GitHub](https://github.com/EttoreCSenatore/caderneta/releases); o teste de fumaça mostra a versão no ar (veja [Versões e Novidades](./versoes.md)). As migrações rodam sozinhas (`migrate`). **Faça um backup antes** de atualizar. Para voltar atrás, restaure o backup e a versão anterior do código.

## Segurança da máquina (responsabilidade de quem hospeda)

- Atualizações automáticas de segurança do sistema; acesso por **chave SSH**, sem senha; firewall liberando só 22 (restrito), 80 e 443.
- Disco do servidor **cifrado** (volume), quando o provedor oferecer.
- Cópias de segurança **em outro lugar** (outra conta ou região).
- Quem tem acesso ao servidor enxerga o banco e as chaves: limite e registre esses acessos (veja o [plano de incidentes](./documentos-de-conformidade.md)).

## Limites conhecidos

- Esta receita foi **testada localmente** (pilha completa com HTTPS de teste), **não** numa hospedagem real: a hospedagem do piloto ainda não foi escolhida.
- A conversão de DOCX para PDF (LibreOffice) **não vem na imagem**: anexos DOCX de provas precisam ser enviados em PDF até que se decida incluí-la.
- Alta disponibilidade, múltiplas máquinas e S3 para arquivos ficam para depois do piloto.
