#!/bin/sh
# Cria o papel usado pela API. Ele NÃO é dono das tabelas, então o Row-Level Security vale para ele.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE ROLE caderneta_app LOGIN PASSWORD '${APP_DB_PASSWORD}' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
CREATE DATABASE caderneta_test OWNER caderneta_owner;
GRANT CONNECT ON DATABASE caderneta TO caderneta_app;
GRANT CONNECT ON DATABASE caderneta_test TO caderneta_app;
SQL
for db in caderneta caderneta_test; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<SQL
GRANT USAGE ON SCHEMA public TO caderneta_app;
CREATE EXTENSION IF NOT EXISTS citext;
SQL
done
