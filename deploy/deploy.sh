#!/usr/bin/env bash
# Git-based deploy script for VPS — run on the server after initial setup.
# Usage:
#   ./deploy/deploy.sh          # pull + rebuild
#   ./deploy/deploy.sh --first  # first-time: create .env from template if missing

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FIRST=false
if [[ "${1:-}" == "--first" ]]; then
  FIRST=true
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

echo "==> Pulling latest from git..."
git pull --ff-only origin main

echo "==> Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Status:"
docker compose -f docker-compose.prod.yml ps

echo "==> Health check:"
sleep 5
curl -sf http://127.0.0.1:8010/health && echo " Backend OK" || echo " Backend not ready yet (may still be starting)"

echo "Done. Future deploys: cd /opt/repolens && ./deploy/deploy.sh"
