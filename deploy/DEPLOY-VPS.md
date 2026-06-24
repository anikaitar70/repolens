# Deploy RepoLens on OVH VPS — https://rl.anikait.page

Install path: **`/opt/repolens`** (not home directory).

## DNS

| Type | Name | Value |
|------|------|-------|
| A | rl | 51.79.251.45 |

## First-time setup (on VPS)

```bash
ssh ubuntu@51.79.251.45

sudo mkdir -p /opt/repolens
sudo chown ubuntu:ubuntu /opt/repolens

git clone https://github.com/anikaitar70/repolens.git /opt/repolens
cd /opt/repolens
chmod +x deploy/deploy.sh
cp deploy/env.production.example .env

chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

`.env` is preconfigured for `https://rl.anikait.page`.

## Nginx (new site only)

`client_max_body_size` must be at least **150m** so large ZIP uploads are not rejected with HTTP 413 before they reach the backend.

```bash
sudo cp /opt/repolens/deploy/nginx/repolens.conf.example /etc/nginx/sites-available/repolens
sudo ln -sf /etc/nginx/sites-available/repolens /etc/nginx/sites-enabled/repolens
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d rl.anikait.page
```

**Yoga stack (current production):** RepoLens is proxied from `/opt/yoga/nginx/conf.d/repolens.conf`. After deploy, ensure that file includes `client_max_body_size 150m;` inside the `server` block, then reload:

```bash
docker exec yoga-nginx-1 nginx -s reload
```

## Git deploy (after you push to GitHub)

```bash
ssh ubuntu@51.79.251.45
cd /opt/repolens
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

## Verify

- https://rl.anikait.page
- `curl https://rl.anikait.page/health`

## Troubleshooting

### `no space left on device` during backend build

The backend uses `sentence-transformers`, which pulls in PyTorch. The Dockerfile installs **CPU-only** PyTorch to avoid huge CUDA libraries. If a build still fails:

```bash
df -h
docker system df

# Free Docker build cache and unused images (safe if yoga/repolens can be rebuilt)
docker builder prune -af
docker image prune -af

cd /opt/repolens
git pull
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

Also set in `/opt/repolens/.env`:

```
MAX_UPLOAD_SIZE=157286400
```

And in `/opt/yoga/nginx/conf.d/repolens.conf`:

```
client_max_body_size 150m;
```

Then `docker exec yoga-nginx-1 nginx -s reload`.

### 502 Bad Gateway on https://rl.anikait.page

Usually the RepoLens containers are down, or yoga-nginx cannot reach them.

```bash
cd /opt/repolens
docker compose -f docker-compose.prod.yml ps

# Should return {"status":"ok"}
curl -s http://127.0.0.1:8010/health
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3010/

docker logs repolens-backend-1 --tail 80
docker logs repolens-frontend-1 --tail 80
```

**yoga nginx must proxy to container names**, not `127.0.0.1` (that points inside the nginx container itself). Use `deploy/nginx/repolens-yoga.conf.example` as the template for `/opt/yoga/nginx/conf.d/repolens.conf`.

After any deploy, reconnect the yoga network and verify:

```bash
cd /opt/repolens
git pull
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

Or manually:

```bash
YOGA_NET=$(docker inspect yoga-nginx-1 --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' | awk '{print $1}')
docker network connect "$YOGA_NET" repolens-backend-1 2>/dev/null || true
docker network connect "$YOGA_NET" repolens-frontend-1 2>/dev/null || true
docker exec yoga-nginx-1 wget -qO- http://repolens-frontend-1:3000/ | head
docker exec yoga-nginx-1 nginx -s reload
```
