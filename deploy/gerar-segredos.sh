#!/bin/sh
# Imprime segredos novos no formato do .env. Guarde uma cópia FORA do servidor (cofre de senhas).
# A chave de dados (CADERNETA_DATA_KEY) cifra saúde, 2FA e arquivos: sem ela os dados não abrem, nem nos backups.
set -eu
gen() { python3 -c "import secrets,sys; print(secrets.token_urlsafe(int(sys.argv[1])))" "$1"; }
echo "OWNER_DB_PASSWORD=$(gen 24)"
echo "APP_DB_PASSWORD=$(gen 24)"
echo "CADERNETA_DATA_KEY=$(python3 -c 'import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')"
echo "# senha do backup (use em BACKUP_PASSPHRASE_FILE, separada da chave de dados): $(gen 32)" >&2
