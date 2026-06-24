#!/usr/bin/env bash
# Git-based deploy script for VPS — run on the server after initial setup.
# Usage:
#   ./deploy/deploy.sh          # pull + rebuild
#   ./deploy/deploy.sh --first  # first-time: create .env from template if missing

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE="docker compose -f docker-compose.prod.yml"

if [[ "${1:-}" == "--first" ]]; then
  :
fi

if [[ ! -f .env ]]; then
  if [[ -f deploy/env.production.example ]]; then
    cp deploy/env.production.example .env
    echo "Created .env from deploy/env.production.example"
    echo "Edit .env (NEXT_PUBLIC_API_URL, CORS_ORIGINS) then re-run."
    exit 1
  else
    echo "Missing .env — copy deploy/env.production.example to .env and configure."
    exit 1
  fi
fi

connect_yoga_network() {
  if ! docker ps --format '{{.Names}}' | grep -qx 'yoga-nginx-1'; then
    echo "==> yoga-nginx-1 not found — skipping Docker network connect (host-port nginx?)"
    return 0
  fi

  local yoga_net
  yoga_net=$(docker inspect yoga-nginx-1 --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' | awk '{print $1}')
  if [[ -z "$yoga_net" ]]; then
    echo "WARNING: could not detect yoga Docker network"
    return 0
  fi

  echo "==> Connecting RepoLens containers to yoga network: $yoga_net"
  for container in repolens-backend-1 repolens-frontend-1; do
    if ! docker ps --format '{{.Names}}' | grep -qx "$container"; then
      echo "  skip $container (not running)"
      continue
    fi
    if docker inspect "$container" --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' | grep -qE "(^| )${yoga_net}( |$)"; then
      echo "  $container already on $yoga_net"
    else
      docker network connect "$yoga_net" "$container"
      echo "  connected $container"
    fi
  done
}

echo "==> Pulling latest from git..."
if ! git pull --ff-only origin main; then
  echo "==> Local changes blocked pull; resetting deploy/deploy.sh and retrying..."
  git checkout -- deploy/deploy.sh 2>/dev/null || true
  git pull --ff-only origin main
fi

echo "==> Building and starting containers..."
$COMPOSE up -d --build

connect_yoga_network

echo "==> Status:"
$COMPOSE ps

echo "==> Health check (host ports):"
sleep 8
BACKEND_OK=false
FRONTEND_OK=false

if curl -sf http://127.0.0.1:8010/health >/dev/null; then
  echo "  Backend OK  (127.0.0.1:8010)"
  BACKEND_OK=true
else
  echo "  Backend FAIL (127.0.0.1:8010) — see: docker logs repolens-backend-1 --tail 80"
fi

if curl -sf -o /dev/null http://127.0.0.1:3010/; then
  echo "  Frontend OK (127.0.0.1:3010)"
  FRONTEND_OK=true
else
  echo "  Frontend FAIL (127.0.0.1:3010) — see: docker logs repolens-frontend-1 --tail 80"
fi

if docker ps --format '{{.Names}}' | grep -qx 'yoga-nginx-1'; then
  echo "==> Health check (from yoga-nginx container):"
  if docker exec yoga-nginx-1 wget -qO- http://repolens-backend-1:8000/health 2>/dev/null | grep -q ok; then
    echo "  yoga -> repolens-backend-1 OK"
  else
    echo "  yoga -> repolens-backend-1 FAIL — check /opt/yoga/nginx/conf.d/repolens.conf uses container names"
    echo "  See deploy/nginx/repolens-yoga.conf.example and re-run this script."
  fi
  if docker exec yoga-nginx-1 wget -qO- http://repolens-frontend-1:3000/ 2>/dev/null | head -c 20 >/dev/null; then
    echo "  yoga -> repolens-frontend-1 OK"
  else
    echo "  yoga -> repolens-frontend-1 FAIL"
  fi
fi

if [[ "$BACKEND_OK" == false || "$FRONTEND_OK" == false ]]; then
  echo ""
  echo "Deploy finished but services are unhealthy. Common fixes:"
  echo "  docker builder prune -af && docker image prune -af   # if disk was full"
  echo "  $COMPOSE logs backend --tail 100"
  echo "  $COMPOSE up -d --build"
  exit 1
fi

echo "Done. Site: https://rl.anikait.page"
