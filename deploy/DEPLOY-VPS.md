# Deploy RepoLens on OVH VPS (alongside existing website)

This guide adds RepoLens **without touching** your existing nginx site or certbot certificates.

## Architecture

```
Internet
   │
   ▼
nginx (existing + NEW repolens site block)
   │
   ├── your-existing-site.com  → existing app (unchanged)
   │
   └── repolens.YOURDOMAIN.com → 127.0.0.1:3010 (frontend)
                                 127.0.0.1:8010 (backend /api)
```

RepoLens Docker containers bind to **localhost only** (ports 3010 and 8010), so they never conflict with ports 80/443.

## Prerequisites

- Ubuntu VPS with Docker and Docker Compose plugin
- nginx + certbot already running (your existing site)
- A **subdomain** DNS A record → `51.79.251.45` (e.g. `repolens.yourdomain.com`)
- At least **4 GB RAM** recommended (semantic duplicate detection loads an ML model)

## Step 1 — DNS

In your domain registrar, add:

| Type | Name | Value |
|------|------|-------|
| A | repolens | 51.79.251.45 |

Wait a few minutes for DNS propagation.

## Step 2 — Clone from GitHub (recommended)

```bash
ssh ubuntu@51.79.251.45

git clone https://github.com/anikaitar70/repolens.git ~/repolens
cd ~/repolens
chmod +x deploy/deploy.sh
cp deploy/env.production.example .env
nano .env   # set NEXT_PUBLIC_API_URL and CORS_ORIGINS
```

## Step 2 (alt) — Copy code manually

```bash
scp -r ./repolens ubuntu@51.79.251.45:~/repolens
```

## Step 3 — Install Docker (if not already installed)

```bash
ssh ubuntu@51.79.251.45

# Skip if docker already works
docker --version
docker compose version
```

If missing:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker ubuntu
# Log out and back in for group change
```

## Step 4 — Configure environment

```bash
cd ~/repolens
cp deploy/env.production.example .env
nano .env
```

Set:

```env
NEXT_PUBLIC_API_URL=https://repolens.YOURDOMAIN.com
CORS_ORIGINS=https://repolens.YOURDOMAIN.com
```

`GROQ_API_KEY` is optional — users can use BYOK in the browser.

## Step 5 — Build and start containers

```bash
cd ~/repolens
./deploy/deploy.sh --first
# After editing .env:
./deploy/deploy.sh
```

Or manually:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First build takes 10–20 minutes (PyTorch + sentence-transformers).

Verify:

```bash
curl http://127.0.0.1:8010/health
curl -I http://127.0.0.1:3010
docker compose -f docker-compose.prod.yml ps
```

## Step 6 — Add NEW nginx site (do not edit existing config)

```bash
sudo cp ~/repolens/deploy/nginx/repolens.conf.example /etc/nginx/sites-available/repolens
sudo nano /etc/nginx/sites-available/repolens
# Change repolens.YOURDOMAIN.com to your real subdomain

sudo ln -s /etc/nginx/sites-available/repolens /etc/nginx/sites-enabled/repolens
sudo nginx -t
sudo systemctl reload nginx
```

**Important:** Only add the new symlink. Do not modify your existing site file in `sites-enabled`.

## Step 7 — SSL for the new subdomain only

```bash
sudo certbot --nginx -d repolens.YOURDOMAIN.com
```

Certbot will add SSL to the **repolens** config only. Your existing site's certificate is untouched.

## Step 8 — Test

Open `https://repolens.YOURDOMAIN.com` in a browser.

- Upload a sample ZIP
- Configure AI key in AI Settings (stored in browser only)
- Or use Prompt Export without a key

## Updating after code changes

```bash
cd ~/repolens
./deploy/deploy.sh
```

This runs `git pull` and rebuilds containers.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 502 Bad Gateway | `docker compose -f docker-compose.prod.yml ps` — wait for backend health |
| CORS error | `CORS_ORIGINS` in `.env` must match exact public URL (https) |
| Upload fails | nginx `client_max_body_size 26m` in repolens.conf |
| Out of memory | Upgrade VPS RAM or set `DUPLICATE_DETECTION_ENABLED=false` in `.env` |
| Existing site broken | You edited wrong nginx file — restore from backup |

## Security notes

- BYOK API keys are sent per request and not stored server-side
- Do not commit `.env` to git
- Consider `ufw` — only 22, 80, 443 need to be public

## What stays unchanged

- Existing nginx site config files
- Existing certbot certificates for other domains
- Ports 80/443 (nginx still owns them)
- Your other website's Docker processes / services
