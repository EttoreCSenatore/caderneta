#!/bin/sh
# Teste de fumaça da instalação: o que precisa estar certo logo depois de subir (e depois de cada atualização).
#   sh smoke.sh https://caderneta.suaescola.com.br
#   SMOKE_INSECURE=1 sh smoke.sh https://localhost:18443     # certificado de teste local
set -u
BASE="${1:?use: sh smoke.sh https://seu-dominio}"
CURL="curl -sS --max-time 15 ${SMOKE_INSECURE:+-k}"
falhas=0
ok() { echo "ok:     $1"; }
ruim() { echo "FALHA:  $1"; falhas=$((falhas + 1)); }
codigo() { $CURL -o /dev/null -w '%{http_code}' "$@"; }
cabecalho() { $CURL -D - -o /dev/null "$1" | tr -d '\r' | grep -i "^$2:" | head -1; }

[ "$(codigo "$BASE/")" = "200" ] && ok "site responde" || ruim "site não responde 200"
[ "$(codigo "$BASE/qualquer/rota")" = "200" ] && ok "rotas do app caem no index" || ruim "fallback do app web"
$CURL "$BASE/api/saude" | grep -q '"ok":true' && ok "API saudável" || ruim "API não saudável"
versao=$($CURL "$BASE/api/saude" | sed -n 's/.*"versao":"\([0-9.]*\)".*/\1/p')
[ -n "$versao" ] && ok "versão $versao no ar" || ruim "API não informa a versão"
[ "$(codigo "$BASE/api/docs")" = "404" ] && ok "documentação da API desligada" || ruim "documentação da API está acessível"
[ "$(codigo -X POST -H 'Content-Type: application/json' -d '{}' "$BASE/api/auth/login")" = "403" ] && ok "CSRF: POST sem cabeçalho é recusado" || ruim "CSRF não recusou"
cabecalho "$BASE/" "strict-transport-security" | grep -q "max-age" && ok "HSTS no site" || ruim "sem HSTS no site"
cabecalho "$BASE/" "content-security-policy" | grep -q "default-src 'self'" && ok "CSP no site" || ruim "sem CSP no site"
cabecalho "$BASE/api/saude" "content-security-policy" | grep -q "default-src 'none'" && ok "CSP vazia na API" || ruim "API sem CSP vazia"
cabecalho "$BASE/sw.js" "cache-control" | grep -qi "no-cache" && ok "service worker sem cache" || ruim "service worker pode ficar em cache"
$CURL "$BASE/api/legal/privacidade" | grep -q '"versao"' && ok "política de privacidade pública" || ruim "política não carrega"
if [ "$falhas" -eq 0 ]; then echo "TUDO CERTO"; else echo "$falhas falha(s)"; exit 1; fi
