---
title: Revisão de segurança (M8.1)
---

# Revisão de segurança do código (M8.1)

Revisão interna, feita por leitura do código, ferramentas automáticas e testes. **Não substitui** o teste de intrusão por terceiro nem o parecer jurídico, que continuam no fechamento do M8.

## O que foi verificado e o resultado

| Tema | Resultado |
|---|---|
| **Dependências** | `pip-audit` e `npm audit` sem vulnerabilidades conhecidas; rodam no CI a cada alteração. O CI gera o **SBOM** (CycloneDX) da API e do app web como artefato |
| **Cadeia de suprimentos** | O **Dependabot** propõe atualizações em PRs agrupados, com espera de 7 dias para versões novas (correções de segurança chegam na hora). As **Actions** ficam fixadas pelo commit e as **imagens Docker** pelo digest; `scripts/checar-fixacao.py` reprova a CI se algo entrar sem fixação ou se a mesma imagem divergir entre CI, desenvolvimento e produção |
| **Análise estática** | `ruff` com regras de segurança (`S`, estilo Bandit) sem achados; sem SQL montado por texto com dado do usuário (tudo via ORM ou parâmetros) |
| **Segredos no repositório** | Nenhum arquivo `.env`, chave ou token versionado. Os valores de demonstração (senha e segredo 2FA do seed) são fictícios e só existem no ambiente local |
| **Autenticação** | Senhas com Argon2id; tempo constante mesmo para e-mail inexistente; bloqueio progressivo por conta; sessão com token opaco (só o hash no banco), cookie `HttpOnly`, `SameSite=Lax` e `Secure` obrigatório em produção; 2FA obrigatório para a equipe |
| **Autorização** | Papel e vínculo checados na API e, por baixo, **Row-Level Security** no PostgreSQL. Um teste percorre **todas as rotas** e reprova se alguma ficar sem login fora da lista de rotas públicas conhecida (7: entrar, recuperar senha, convite, iCal por link secreto e conferência do histórico) |
| **CSRF** | Cabeçalho `X-Caderneta` exigido em toda requisição que altera dados, sem CORS habilitado |
| **Uploads** | Validados pelo conteúdo, antivírus (falha fechada), EXIF removido, cifrados em repouso, download por link assinado de 5 minutos |
| **Cabeçalhos da API** | `nosniff`, `no-store`, `no-referrer`, `X-Frame-Options: DENY`, `Cross-Origin-Resource-Policy`, CSP vazia nas respostas JSON e **HSTS** em produção |

## O que foi corrigido nesta etapa

- **Limite de taxa** (antes não havia): login por IP (30 a cada 15 min), recuperação de senha (3 por e-mail e 20 por IP a cada hora, **sempre responde 204** para não revelar se o e-mail existe), redefinição, convites e a conferência pública do histórico (20 por minuto por IP; antes só o tamanho do código protegia). O contador é gravado com um **hash** do IP ou do e-mail, nunca o valor, e é apagado depois de 2 dias
- **Código 2FA não vale duas vezes**: quem espiar o código de 6 dígitos não consegue reutilizá-lo no mesmo intervalo de 30 segundos
- **Conta do usuário** (nova página *Minha conta*): trocar a senha (pede a atual, derruba as outras sessões), ver os **aparelhos conectados** e **sair em todos os aparelhos**, que também cancela o push de todos. É o procedimento para celular perdido ou emprestado
- Novos cabeçalhos de segurança na API e HSTS em produção

## Resolvido depois (M8.5 e M9)

- **Cabeçalhos do site:** o Caddy da [implantação](./implantacao.md) envia CSP, HSTS, `nosniff`, `Referrer-Policy` e `Permissions-Policy`, e o log dele não guarda caminho nem query string (verificado no navegador, sem violação de CSP).
- **Proxy reverso e IP real:** a imagem da API roda com `--proxy-headers`, e só o proxy alcança a API.
- **Rotação da chave de dados:** feita (`rotacionar-chave`); veja [Backups, chaves e logs](./backups-chaves-e-logs.md).

## Fica para o fechamento do M8 e para a implantação real

- **Teste de intrusão por terceiro**, antes do piloto.
- **2FA para professores:** hoje é obrigatório só para a equipe (decisão do responsável). Professores veem nomes, notas, anotações e mensagens (mas só o **alerta resumido** de saúde). Reavaliar no parecer e no RIPD.
- **Senhas:** não há lista de senhas vazadas ou comuns (só tamanho mínimo e mistura de tipos).
- **Recuperação do 2FA** (celular perdido pela equipe): hoje depende de a direção refazer o acesso; falta um fluxo com códigos de reserva.
- **Monitoramento e alertas:** a ferramenta existe (`deploy/verificar.sh`), falta configurá-la na hospedagem real.

## Checklist OWASP Top 10 (2021)

| Item | Situação |
|---|---|
| A01 Controle de acesso quebrado | Coberto (papel + vínculo + RLS + teste de todas as rotas). Pen test confirma |
| A02 Falhas criptográficas | Argon2id, AES-256-GCM para saúde e arquivos, TLS na implantação, rotação de chaves feita |
| A03 Injeção | ORM e parâmetros; sem achados do `ruff S` |
| A04 Design inseguro | Privacidade desde a concepção; limites de taxa adicionados |
| A05 Configuração incorreta | Produção exige chave, ClamAV, cookie seguro e caminho absoluto; documentação da API desligada; o Caddy do app envia os cabeçalhos |
| A06 Componentes vulneráveis | `pip-audit` e `npm audit` no CI, Dependabot, SBOM e auditoria de licenças |
| A07 Falhas de autenticação | Bloqueio, 2FA, limite por IP, sem reuso de código. Falta lista de senhas fracas e códigos de reserva |
| A08 Integridade de software e dados | Dependências travadas por lock; histórico emitido com código de conferência |
| A09 Falhas de log e monitoramento | Auditoria de ações sensíveis e de login. Script de verificação pronto; falta configurar na hospedagem (M9) |
| A10 SSRF | O único acesso a endereço externo vindo de dado do usuário é o push, com lista de hosts permitidos |
