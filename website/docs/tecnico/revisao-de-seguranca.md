---
title: Revisão de segurança (M8.1)
---

# Revisão de segurança do código (M8.1)

Revisão interna, feita por leitura do código, ferramentas automáticas e testes. **Não substitui** o teste de intrusão por terceiro nem o parecer jurídico, que continuam no fechamento do M8.

## O que foi verificado e o resultado

| Tema | Resultado |
|---|---|
| **Dependências** | `pip-audit` e `npm audit` sem vulnerabilidades conhecidas; rodam no CI a cada alteração. O CI gera o **SBOM** (CycloneDX) da API e do app web como artefato |
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

## Fica para a implantação (M9) e para o fechamento do M8

- **Proxy reverso e IP real:** rodar a API com `--proxy-headers --forwarded-allow-ips=<IP do proxy>`; sem isso o limite de taxa enxerga o IP do proxy
- **Cabeçalhos do site (app web):** o servidor que entrega o app precisa enviar `Content-Security-Policy` (por exemplo `default-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'`), `Strict-Transport-Security`, `X-Content-Type-Options: nosniff` e `Referrer-Policy: no-referrer`. O Vite entrega estes arquivos sem esses cabeçalhos
- **Logs do proxy:** o link do calendário (iCal) leva um token na URL; configurar o proxy para **não registrar** esse caminho
- **Rotação da chave de dados** (hoje há uma única chave, sem versão) e guarda segura da chave: T14, no M8.5
- **Teste de intrusão por terceiro**, antes do piloto
- **2FA para professores:** hoje é obrigatório só para a equipe. Professores veem nomes, notas, anotações e mensagens (mas só o **alerta resumido** de saúde). Decidir com o parecer jurídico e o RIPD se o 2FA passa a valer para eles
- **Senhas:** não há lista de senhas vazadas ou comuns (só tamanho mínimo e mistura de tipos)
- **Recuperação do 2FA** (celular perdido pela equipe): hoje depende de a direção refazer o acesso; falta um fluxo com códigos de reserva

## Checklist OWASP Top 10 (2021)

| Item | Situação |
|---|---|
| A01 Controle de acesso quebrado | Coberto (papel + vínculo + RLS + teste de todas as rotas). Pen test confirma |
| A02 Falhas criptográficas | Argon2id, AES-256-GCM para saúde e arquivos, TLS na implantação. Falta rotação de chaves (M8.5) |
| A03 Injeção | ORM e parâmetros; sem achados do `ruff S` |
| A04 Design inseguro | Privacidade desde a concepção; limites de taxa adicionados |
| A05 Configuração incorreta | Produção exige chave, ClamAV, cookie seguro e caminho absoluto; documentação da API desligada. Falta o servidor do app (M9) |
| A06 Componentes vulneráveis | `pip-audit` e `npm audit` no CI, SBOM e auditoria de licenças |
| A07 Falhas de autenticação | Bloqueio, 2FA, limite por IP, sem reuso de código. Falta lista de senhas fracas e códigos de reserva |
| A08 Integridade de software e dados | Dependências travadas por lock; histórico emitido com código de conferência |
| A09 Falhas de log e monitoramento | Auditoria de ações sensíveis e de login. Falta monitoramento e alertas (M8.5/M9) |
| A10 SSRF | O único acesso a endereço externo vindo de dado do usuário é o push, com lista de hosts permitidos |
