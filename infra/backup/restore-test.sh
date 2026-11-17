#!/bin/sh
# Teste de restauração: abre o backup, restaura num banco TEMPORÁRIO, confere os dados e, principalmente, confere
# que as CHAVES DE DADOS conseguem abrir o que está cifrado (saúde, 2FA e arquivos). Backup que não abre é inútil.
#
#   BACKUP_FILE=/var/backups/caderneta/caderneta-XXXX.tar.gpg BACKUP_PASSPHRASE_FILE=... \
#   OWNER_URL_BASE=postgresql+psycopg://caderneta_owner:SENHA@host:5432 \
#   CADERNETA_DATA_KEY=... CADERNETA_DATA_KEYS_ANTIGAS=... PGHOST=... PGUSER=... PGPASSWORD=... \
#   sh infra/backup/restore-test.sh
#
# Variáveis: BACKUP_FILE, BACKUP_PASSPHRASE_FILE, OWNER_URL_BASE (sem o nome do banco), PG* ; PG_PREFIX (opcional,
# como no backup.sh); PYTHON (padrão python3, com a API instalada); SCRATCH_DB (padrão caderneta_restore_test).
# NUNCA aponte para o banco de produção: o script cria e APAGA o banco temporário SCRATCH_DB.
set -eu
umask 077
: "${BACKUP_FILE:?defina BACKUP_FILE}" "${BACKUP_PASSPHRASE_FILE:?defina BACKUP_PASSPHRASE_FILE}" "${OWNER_URL_BASE:?defina OWNER_URL_BASE}"
SCRATCH_DB="${SCRATCH_DB:-caderneta_restore_test}"
PG_PREFIX="${PG_PREFIX:-}"
PYTHON="${PYTHON:-python3}"
case "$SCRATCH_DB" in caderneta|caderneta_prod|*prod*) echo "recusado: SCRATCH_DB parece produção" >&2; exit 2;; esac
TMP=$(mktemp -d "${TMPDIR:-/tmp}/caderneta-restore.XXXXXX")
cleanup() {
  # shellcheck disable=SC2086
  $PG_PREFIX psql -v ON_ERROR_STOP=1 -d postgres -c "DROP DATABASE IF EXISTS $SCRATCH_DB" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

gpg --batch --yes --quiet --pinentry-mode loopback --passphrase-file "$BACKUP_PASSPHRASE_FILE" --decrypt --output "$TMP/pacote.tar" "$BACKUP_FILE"
tar -C "$TMP" -xf "$TMP/pacote.tar"
( cd "$TMP" && sha256sum -c SHA256SUMS >/dev/null ) && echo "ok: backup abriu e as somas conferem"
mkdir -p "$TMP/storage" && tar -C "$TMP/storage" -xf "$TMP/arquivos.tar"

# shellcheck disable=SC2086
$PG_PREFIX psql -v ON_ERROR_STOP=1 -d postgres -c "DROP DATABASE IF EXISTS $SCRATCH_DB" -c "CREATE DATABASE $SCRATCH_DB" >/dev/null
# shellcheck disable=SC2086
$PG_PREFIX pg_restore --no-owner --no-privileges --dbname "$SCRATCH_DB" < "$TMP/banco.dump"
# shellcheck disable=SC2086
LINHAS=$($PG_PREFIX psql -At -d "$SCRATCH_DB" -c "SELECT (SELECT count(*) FROM escola) || ' escolas, ' || (SELECT count(*) FROM aluno) || ' alunos, ' || (SELECT count(*) FROM usuario) || ' usuarios'")
echo "ok: banco restaurado: $LINHAS"

# As chaves abrem tudo? (`--simular` não grava nada; falha se algum conteúdo não abrir com nenhuma chave.)
CADERNETA_OWNER_DATABASE_URL="$OWNER_URL_BASE/$SCRATCH_DB" CADERNETA_STORAGE_DIR="$TMP/storage" \
  "$PYTHON" -m app.cli rotacionar-chave --simular --exigir-arquivos
echo "ok: as chaves de dados abrem o conteúdo cifrado do backup"
echo "Lembrete: ao restaurar de verdade, rode 'python -m app.cli notificar' para reaplicar a retenção e revise os pedidos de eliminação posteriores ao backup."
