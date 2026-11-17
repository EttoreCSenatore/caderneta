#!/bin/sh
# Verificação periódica (cron a cada 5 a 15 minutos): site no ar, backup recente, disco, banco.
# Sai com erro e escreve o motivo se algo estiver errado; se ALERTA_URL existir (healthchecks.io, ntfy etc.), avisa lá.
#   */10 * * * * BASE_URL=https://caderneta.suaescola.com.br BACKUP_DIR=/var/backups/caderneta ALERTA_URL=... sh /opt/caderneta/deploy/verificar.sh
set -u
BASE_URL="${BASE_URL:?defina BASE_URL}"
BACKUP_DIR="${BACKUP_DIR:-}"
BACKUP_MAX_HORAS="${BACKUP_MAX_HORAS:-26}"
DISCO_MAX="${DISCO_MAX:-85}"
COMPOSE="${COMPOSE:-docker compose -f $(dirname "$0")/docker-compose.prod.yml}"
problemas=""
add() { problemas="$problemas\n- $1"; }

curl -fsS --max-time 15 ${VERIFICAR_INSECURE:+-k} "$BASE_URL/api/saude" | grep -q '"ok":true' || add "API fora do ar ou não saudável ($BASE_URL/api/saude)"
if [ -n "$BACKUP_DIR" ]; then
  if [ -f "$BACKUP_DIR/ultimo-backup.txt" ] && [ -n "$(find "$BACKUP_DIR/ultimo-backup.txt" -mmin "-$((BACKUP_MAX_HORAS * 60))" 2>/dev/null)" ]; then :; else add "backup atrasado: nada em $BACKUP_DIR nas últimas $BACKUP_MAX_HORAS horas"; fi
fi
uso=$(df -P / | awk 'NR==2 {gsub("%",""); print $5}')
[ "${uso:-0}" -lt "$DISCO_MAX" ] || add "disco em ${uso}% (limite $DISCO_MAX%)"
$COMPOSE exec -T db pg_isready -U caderneta_owner -d caderneta >/dev/null 2>&1 || add "banco não responde"
$COMPOSE ps --status exited --format '{{.Service}}' 2>/dev/null | grep -qv '^migrate$' && add "algum serviço parou: $($COMPOSE ps --status exited --format '{{.Service}}' | grep -v '^migrate$' | tr '\n' ' ')"

if [ -z "$problemas" ]; then
  [ -n "${ALERTA_URL_OK:-}" ] && curl -fsS --max-time 10 "$ALERTA_URL_OK" >/dev/null 2>&1
  exit 0
fi
printf "PROBLEMAS em %s:%b\n" "$BASE_URL" "$problemas" >&2
[ -n "${ALERTA_URL:-}" ] && printf "Caderneta: problemas em %s:%b" "$BASE_URL" "$problemas" | curl -fsS --max-time 10 --data-binary @- "$ALERTA_URL" >/dev/null 2>&1
exit 1
