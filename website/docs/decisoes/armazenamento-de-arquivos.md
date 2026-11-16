---
title: "ADR 0004: armazenamento de arquivos"
sidebar_label: "ADR 0004: arquivos"
---

# ADR 0004: arquivos cifrados em disco, atrás de uma interface

- **Status:** aceita (2026-11-16); revisar no M9 (piloto)
- **Contexto:** o M5 precisa guardar provas e trabalhos, que são **sigilosos até a aplicação**. A arquitetura previa armazenamento
  compatível com S3 (MinIO). Subir e operar um serviço extra só para isso, antes de existir um servidor de produção, adiciona
  superfície de ataque e complexidade sem ganho para o desenvolvimento.

## Decisão

1. Os arquivos ficam em um **diretório local** (`CADERNETA_STORAGE_DIR`, uma pasta por escola), **cifrados em repouso com AES-GCM**
   (a mesma chave dos dados sensíveis; o id do arquivo entra como dado associado, então um arquivo trocado de lugar não abre).
2. Todo acesso passa por `app/arquivos.py` (`grava`, `le`, `apaga`). Trocar por S3 compatível exige reescrever só essas três funções.
3. O navegador nunca recebe o caminho: baixa por **link assinado** (HMAC, 5 minutos, preso ao usuário e à escola), e a API **confere
   o acesso de novo** a cada download, que fica na auditoria.
4. A validação olha o **conteúdo**: assinatura PDF ou DOCX, 15 MB, PDF sem JavaScript, anexos ou execução, DOCX sem macros nem
   caminhos inválidos nem "bomba" de descompactação.

## Consequências

- Em desenvolvimento e no piloto de uma escola, um servidor basta. Para mais de um servidor de aplicação (M9), migrar para S3
  compatível, mantendo a cifragem no cliente.
- **Backup:** o diretório precisa entrar no backup junto com o banco, e a **chave de dados** guardada à parte: sem ela os arquivos
  não abrem. Perder a chave significa perder os arquivos.
- A validação é uma barreira, **não um antivírus**. Antes do piloto, avaliar ClamAV ou serviço equivalente (ver `.lgpd/gaps.md`).
- DOCX é aceito como está. A conversão para PDF (para impressão fiel) depende de um conversor no servidor, previsto para depois.
