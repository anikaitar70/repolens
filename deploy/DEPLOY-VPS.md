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

`client_max_body_size` must be at least **100m** so large ZIP uploads are not rejected with HTTP 413 before they reach the backend.

```bash
sudo cp /opt/repolens/deploy/nginx/repolens.conf.example /etc/nginx/sites-available/repolens
sudo ln -sf /etc/nginx/sites-available/repolens /etc/nginx/sites-enabled/repolens
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d rl.anikait.page
```

**Yoga stack (current production):** RepoLens is proxied from `/opt/yoga/nginx/conf.d/repolens.conf`. After deploy, ensure that file includes `client_max_body_size 100m;` inside the `server` block, then reload:

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
