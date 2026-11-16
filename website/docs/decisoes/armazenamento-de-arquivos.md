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
   caminhos inválidos nem "bomba" de descompactação. Anexos de mensagens: PDF, JPG e PNG de até 10 MB.
5. **Antivírus (ClamAV, `clamd`)** em todo upload, com **falha fechada**: se estiver ligado e fora do ar, o arquivo é recusado.
   É **obrigatório em produção** (a API não sobe sem `CADERNETA_ANTIVIRUS=clamav`).
6. **Imagens perdem os metadados** (EXIF, XMP, comentários, datas), que podem trazer localização e o aparelho, algo sensível por serem
   fotos de crianças e famílias.
7. **DOCX vira PDF** com o LibreOffice sem interface (`CADERNETA_CONVERSOR=libreoffice`), uma conversão isolada por upload (pasta temporária,
   perfil novo, ambiente mínimo, limites de CPU e de tamanho, tempo máximo), e o resultado é revalidado como PDF. Só o PDF é guardado, o que
   também elimina o risco do DOCX original.
8. **Retenção:** pedidos são eliminados 365 dias depois da aplicação, rascunhos parados após 90 dias e anexos de mensagens após 365 dias
   (o texto da mensagem fica). Arquivos órfãos no disco são varridos. Tudo pelo worker, com registro `retencao.eliminar` na auditoria.

## Consequências

- Em desenvolvimento e no piloto de uma escola, um servidor basta. Para mais de um servidor de aplicação (M9), migrar para S3
  compatível, mantendo a cifragem no cliente.
- **Backup:** o diretório precisa entrar no backup junto com o banco, e a **chave de dados** guardada à parte: sem ela os arquivos
  não abrem. Perder a chave significa perder os arquivos.
- O LibreOffice entra como dependência do servidor, e processar documentos não confiáveis é uma superfície de ataque. Por isso roda isolado
  por upload e com limites. Em produção, rodar o conversor em um contêiner sem rede é o próximo endurecimento (M8).
- O ClamAV precisa de atualização diária da base de vírus (`freshclam`) e de memória (cerca de 1 GB).
- O prazo de retenção é global por enquanto. Prazos por escola ficam para o M8, junto com o parecer jurídico.
