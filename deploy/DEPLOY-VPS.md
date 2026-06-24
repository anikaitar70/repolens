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
