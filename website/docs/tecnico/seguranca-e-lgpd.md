---
title: Segurança e LGPD
---

# Segurança e LGPD

A Caderneta guarda dados de **crianças e adolescentes**, incluindo **dados de saúde**. Para a LGPD isso significa:
dados de menores devem ser tratados no seu **melhor interesse** (art. 14) e dados de saúde são **sensíveis** (art. 11).
Segurança é requisito desde o primeiro marco, não etapa final.

## Papéis na LGPD

- **Controladora**: a escola, que decide por que e como os dados são usados.
- **Operadora**: quem opera a plataforma, seguindo as instruções da escola (contrato de operação de dados).
- **Titulares**: alunos, responsáveis e funcionários.

## Medidas

### Acesso

- Autenticação com senha forte (Argon2id), limite de tentativas e bloqueio progressivo.
- **2FA (TOTP) obrigatório** para administradores e coordenação; opcional para os demais.
- Convites por link de uso único que expira; sem cadastro aberto.
- Sessões em cookie `HttpOnly`, `Secure`, `SameSite=Lax`, com proteção CSRF e expiração por inatividade.
- **Autorização em duas camadas**: a API checa o perfil e o vínculo; o PostgreSQL aplica Row-Level Security por escola,
  então um erro na API não vaza dados de outra escola.

### Dados

- TLS em todo tráfego; HSTS e CSP restritiva.
- Ficha de saúde e anotações reservadas **criptografadas em nível de campo**, com chave fora do banco.
- Arquivos (provas, atestados) só por URL assinada de curta duração; verificação de tipo e antivírus no upload.
- **Minimização**: CPF e documentos são opcionais; professores veem alertas de saúde resumidos, não laudos.
- Backups diários criptografados, cópia fora do servidor, teste de restauração mensal.
- Hospedagem preferencialmente no **Brasil**.

### Rastreabilidade

- Auditoria só de inserção para: alteração de notas após fechamento, leitura de ficha de saúde, download de provas,
  mudanças de permissão, exportações.
- Logs sem dados pessoais em texto (IDs no lugar de nomes).

### Direitos dos titulares

- Responsável pode ver e corrigir os dados do filho e baixar uma cópia (exportação JSON/PDF).
- **Consentimento específico** de um responsável para dados não essenciais (ex.: foto do aluno).
- Política de retenção: dados de alunos que saíram são anonimizados após o prazo legal de guarda escolar definido
  pela escola; o histórico escolar oficial é mantido.

### Desenvolvimento

- Dependências auditadas no CI (`pip-audit`, `npm audit`), Dependabot e varredura de segredos.
- Testes automatizados de permissão: para cada perfil, o que **não** pode ver.
- Dados fictícios em todos os ambientes que não sejam produção; nunca copiar produção para dev.
- Revisão de segurança antes do piloto (M8): relatório de impacto (RIPD), teste de intrusão básico, checklist OWASP ASVS nível 2.
