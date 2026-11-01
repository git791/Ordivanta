# Ordivanta — Production Deployment Guide

This document specifies the deployment architecture, configuration, and step-by-step instructions for deploying Ordivanta in production.

---

## 1. System Architecture & Prerequisites

Ordivanta comprises two microservices:

```
                      ┌──────────────────────────────────────────────┐
                      │              Incoming HTTPS/443              │
                      └──────────────────────┬───────────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Reverse Proxy  │
                                    │ (Caddy / Nginx) │
                                    └───┬──────────┬──┘
                                        │          │
                 ┌──────────────────────┘          └──────────────────────┐
                 │                                                        │
        ┌────────▼────────┐                                      ┌────────▼────────┐
        │  Next.js 16 UI  │                                      │ FastAPI Backend │
        │   Port 3000     │                                      │   Port 8000     │
        └─────────────────┘                                      └────────┬────────┘
                                                                          │
                                                                 ┌────────▼────────┐
                                                                 │  SQLite / PG    │
                                                                 │ Persistent Data │
                                                                 └─────────────────┘
```

### Resource Requirements
- **CPU:** 2+ vCPUs recommended (HiGHS MILP branch-and-cut solver utilizes multi-threading).
- **RAM:** Minimum 2 GB (4 GB recommended for larger schedules with >100 workers and 24h horizon).
- **Disk:** 10 GB persistent SSD storage for SQLite database, instance caches, and logs.

---

## 2. Option A: Containerized Deployment (Recommended)

Ordivanta includes production-ready Docker configurations:
- [`backend/Dockerfile`](../backend/Dockerfile): Python 3.11 with pre-configured HiGHS solver engine.
- [`frontend/Dockerfile`](../frontend/Dockerfile): Multi-stage Node 20 / Alpine standalone container.
- [`docker-compose.yml`](../docker-compose.yml): Production orchestration with persistent volume and health checks.

### Single-Command Launch

```bash
# 1. Clone repository on target server
git clone https://github.com/git791/Ordivanta.git
cd Ordivanta

# 2. Build and launch services in background
docker compose up -d --build

# 3. Verify services are healthy
docker compose ps
```

Access the application:
- **Frontend Command Center:** `http://<SERVER_IP>:3000`
- **FastAPI Interactive API Docs:** `http://<SERVER_IP>:8000/docs`
- **Health Check Endpoint:** `http://<SERVER_IP>:8000/api/health`

---

## 3. Option B: Cloud PaaS (Render / Railway / Fly.io)

For zero-devops cloud deployments:

### Deploying on Railway / Render

1. **Deploy Backend Service:**
   - Source: GitHub repo root.
   - Root Directory: `backend`
   - Build Command: `pip install -e .`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/api/health`
   - Copy the generated URL (e.g., `https://ordivanta-api.up.railway.app`).

2. **Deploy Frontend Service:**
   - Source: Same GitHub repo.
   - Root Directory: `frontend`
   - Build Command: `pnpm install && pnpm run build`
   - Start Command: `pnpm run start`
   - Environment Variable:
     ```env
     NEXT_PUBLIC_API_BASE_URL=https://ordivanta-api.up.railway.app
     ```

---

## 4. Option C: Bare Metal / Linux VM (Systemd Services)

If running directly on Ubuntu 22.04 / 24.04 LTS:

### Step 1: Install System Dependencies

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip curl nodejs npm
sudo npm install -g pnpm
```

### Step 2: Configure Backend as a Systemd Service

Create `/etc/systemd/system/ordivanta-backend.service`:

```ini
[Unit]
Description=Ordivanta Scheduling Optimization Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/ordivanta/backend
ExecStart=/opt/ordivanta/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
Environment=DATABASE_URL=sqlite+aiosqlite:////opt/ordivanta/data/ordivanta.db

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ordivanta-backend
```

### Step 3: Configure Frontend as a Systemd Service

Create `/etc/systemd/system/ordivanta-frontend.service`:

```ini
[Unit]
Description=Ordivanta Next.js Frontend
After=ordivanta-backend.service

[Service]
User=www-data
WorkingDirectory=/opt/ordivanta/frontend
ExecStart=/usr/bin/pnpm run start -p 3000
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable --now ordivanta-frontend
```

---

## 5. SSL / TLS Reverse Proxy Setup (Caddy)

Caddy provides automatic HTTPS with zero certificate maintenance.

Create `/etc/caddy/Caddyfile`:

```caddy
your-domain.com {
    # Next.js Frontend
    reverse_proxy /_next/* 127.0.0.1:3000
    reverse_proxy /logo* 127.0.0.1:3000
    reverse_proxy /plant-facility* 127.0.0.1:3000
    reverse_proxy /favicon.ico 127.0.0.1:3000

    # Backend API endpoints
    reverse_proxy /api/* 127.0.0.1:8000
    reverse_proxy /docs 127.0.0.1:8000
    reverse_proxy /openapi.json 127.0.0.1:8000

    # Catch-all frontend
    reverse_proxy 127.0.0.1:3000
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

---

## 6. Environment Variables Reference

| Variable | Service | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Frontend | `http://localhost:8000` | Backend API URL reachable by browser |
| `DATABASE_URL` | Backend | `sqlite+aiosqlite:///ordivanta.db` | SQLAlchemy async connection string |
| `ENVIRONMENT` | Backend | `production` | Runtime mode (`development` / `production`) |
| `SOLVER_TIMEOUT_DEFAULT` | Backend | `60` | Default solver limit in seconds |

---

## 7. Verification & Post-Deployment Checklist

1. **API Connectivity:**
   ```bash
   curl -s http://localhost:8000/api/health | jq .
   # Expected response: {"status": "ok", "solver_available": true, "solver_name": "HiGHS"}
   ```
2. **Solver Telemetry:**
   Check `/settings` in the UI to confirm that `MILP Solver Engine` reports **Available (Ready for optimization runs)**.
3. **Sample Scenario Test:**
   Navigate to `/schedule`, select `sample_scenario`, choose `MILP`, and run the solver. Confirm that an `OPTIMAL` or `FEASIBLE` roster is generated and renders in the Workforce Timeline Planner.
4. **Data Persistence:**
   Restart the container or service (`docker compose restart backend`) and ensure previously solved schedules and scenarios persist.
