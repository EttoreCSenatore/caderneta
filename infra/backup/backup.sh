#!/bin/sh
# Backup cifrado: banco (pg_dump) + diretório de arquivos cifrados, num único arquivo .tar.gpg (AES-256).
#
#   BACKUP_DIR=/var/backups/caderneta BACKUP_PASSPHRASE_FILE=/etc/caderneta/backup.pass \
#   STORAGE_DIR=/var/lib/caderneta/storage PGHOST=... PGUSER=caderneta_owner PGPASSWORD=... PGDATABASE=caderneta \
#   sh infra/backup/backup.sh
#
# Variáveis: BACKUP_DIR, BACKUP_PASSPHRASE_FILE, STORAGE_DIR (obrigatórias); PG* (conexão); PG_PREFIX (opcional,
# comando que antecede pg_dump, ex.: "docker exec -i caderneta-dev-db-1"); RETENCAO_DIAS (padrão 35);
# REGISTRAR (opcional, comando do CLI da Caderneta, ex.: "docker compose -f deploy/docker-compose.prod.yml exec -T worker
# python -m app.cli"): registra o backup no app, para a direção ver o aviso de backup atrasado (MO.4).
#
# A senha do backup é DIFERENTE da chave de dados e deve ficar guardada fora do servidor de backup.
# Os arquivos de provas e anexos já estão cifrados com a chave de dados; a cifra do backup é uma segunda camada.
set -eu
umask 077
: "${BACKUP_DIR:?defina BACKUP_DIR}" "${BACKUP_PASSPHRASE_FILE:?defina BACKUP_PASSPHRASE_FILE}" "${STORAGE_DIR:?defina STORAGE_DIR}"
RETENCAO_DIAS="${RETENCAO_DIAS:-35}"
PG_PREFIX="${PG_PREFIX:-}"
[ -s "$BACKUP_PASSPHRASE_FILE" ] || { echo "senha do backup ausente ou vazia" >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/caderneta-backup.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
AGORA=$(date -u +%Y%m%dT%H%M%SZ)

# shellcheck disable=SC2086
$PG_PREFIX pg_dump --format=custom --no-owner --no-privileges > "$TMP/banco.dump"
tar -C "$STORAGE_DIR" -cf "$TMP/arquivos.tar" .
( cd "$TMP" && sha256sum banco.dump arquivos.tar > SHA256SUMS && echo "gerado_em=$AGORA" > MANIFESTO )
tar -C "$TMP" -cf "$TMP/pacote.tar" banco.dump arquivos.tar SHA256SUMS MANIFESTO

SAIDA="$BACKUP_DIR/caderneta-$AGORA.tar.gpg"
gpg --batch --yes --quiet --pinentry-mode loopback --passphrase-file "$BACKUP_PASSPHRASE_FILE" \
    --symmetric --cipher-algo AES256 --output "$SAIDA" "$TMP/pacote.tar"
echo "$AGORA" > "$BACKUP_DIR/ultimo-backup.txt"

# Expiração: backup antigo some. Um apagamento feito depois dele (aluno desligado, pedido de eliminação) volta
# se este backup for restaurado: por isso o prazo é curto e a restauração reaplica a retenção (ver restore-test.sh).
find "$BACKUP_DIR" -name 'caderneta-*.tar.gpg' -mtime "+$RETENCAO_DIAS" -delete
echo "backup cifrado: $SAIDA"
if [ -n "${REGISTRAR:-}" ]; then
  # shellcheck disable=SC2086
  $REGISTRAR registrar-backup "$(basename "$SAIDA")" --tamanho "$(wc -c < "$SAIDA")" \
    || echo "aviso: o backup foi feito, mas não consegui registrá-lo no app (REGISTRAR)" >&2
fi
