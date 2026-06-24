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

### Still routes to nirvanayoga.org / wrong site

The VPS can serve the correct HTTPS cert while HTTP still routes to nirvana if **`rl.anikait.page` is listed in `production-ssl.conf`**.

```bash
# Confirm the conflict (rl must only appear in repolens.conf)
grep -rn "rl.anikait.page" /opt/yoga/nginx/conf.d/
```

If you see this in `production-ssl.conf`:
```nginx
server_name yoga.anikait.page nirvanayoga.org www.nirvanayoga.org rl.anikait.page;
```

Remove `rl.anikait.page` from that line:

```bash
sed -i 's/ rl\.anikait\.page//' /opt/yoga/nginx/conf.d/production-ssl.conf
grep "server_name" /opt/yoga/nginx/conf.d/production-ssl.conf | head -3

docker exec yoga-nginx-1 nginx -t
docker exec yoga-nginx-1 nginx -s reload
```

You should no longer see:
`conflicting server name "rl.anikait.page" on 0.0.0.0:80, ignored`

Re-apply RepoLens config if needed:

```bash
cd /opt/repolens
cp deploy/nginx/repolens-yoga.conf.example /opt/yoga/nginx/conf.d/repolens.conf
docker exec yoga-nginx-1 nginx -t && docker exec yoga-nginx-1 nginx -s reload
```

Run the bundled checker:

```bash
cd /opt/repolens
bash deploy/verify-rl-nginx.sh
```

From your **local PC** (not VPS), also check DNS/IPv6:

```bash
nslookup rl.anikait.page
curl -4 -I https://rl.anikait.page/
curl -4 -I http://rl.anikait.page/    # should 301 to https://rl.anikait.page/
```

If local `curl -4` shows the wrong cert but VPS curl is correct, flush browser cache or test in incognito.

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

**yoga nginx must proxy to container names**, not `127.0.0.1` (that points inside the nginx container itself). Use `deploy/nginx/repolens-yoga.conf.example` as the template for `/opt/yoga/nginx/conf.d/repolens.conf` — it includes both `80 -> 443` redirect and a dedicated `443 ssl` block for `rl.anikait.page`.

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
