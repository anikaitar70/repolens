#!/usr/bin/env bash
# Verify rl.anikait.page nginx routing on the yoga VPS.
# Usage: bash deploy/verify-rl-nginx.sh

set -euo pipefail

YOGA_CONF_DIR="${YOGA_CONF_DIR:-/opt/yoga/nginx/conf.d}"
DOMAIN="rl.anikait.page"

echo "==> DNS"
echo -n "  A:    "; dig +short A "$DOMAIN" | tr '\n' ' '; echo
echo -n "  AAAA: "; dig +short AAAA "$DOMAIN" | tr '\n' ' '; echo
if dig +short AAAA "$DOMAIN" | grep -q .; then
  echo "  WARNING: AAAA record exists. If it points elsewhere, browsers may route to the wrong host."
fi

echo ""
echo "==> TLS certificate (SNI=$DOMAIN)"
echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null \
  | openssl x509 -noout -subject -ext subjectAltName

echo ""
echo "==> HTTPS response headers"
curl -sI "https://$DOMAIN/" | sed -n '1,12p'

echo ""
echo "==> nginx configs mentioning $DOMAIN"
if [[ -d "$YOGA_CONF_DIR" ]]; then
  grep -rn "$DOMAIN" "$YOGA_CONF_DIR" || echo "  (none found)"
else
  echo "  $YOGA_CONF_DIR not found"
fi

echo ""
echo "==> Duplicate server_name / default_server on 443"
if [[ -d "$YOGA_CONF_DIR" ]]; then
  grep -rnE "listen .*443|server_name|default_server" "$YOGA_CONF_DIR" || true
fi

echo ""
echo "==> From yoga-nginx container"
if docker ps --format '{{.Names}}' | grep -qx 'yoga-nginx-1'; then
  docker exec yoga-nginx-1 wget -qO- "http://repolens-frontend-1:3000/" 2>/dev/null | head -c 80 || true
  echo ""
  if docker exec yoga-nginx-1 wget -qSO- "https://$DOMAIN/" 2>&1 | head -n 15; then
    :
  fi
else
  echo "  yoga-nginx-1 not running"
fi

echo ""
echo "If $DOMAIN appears in more than one .conf file, remove it from all files EXCEPT repolens.conf."
echo "Then: docker exec yoga-nginx-1 nginx -t && docker exec yoga-nginx-1 nginx -s reload"
