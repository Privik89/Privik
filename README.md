## Privik — AI-powered, zero-trust email security (MVP scaffold)

This repository contains the initial scaffold for the Privik backend API: a FastAPI service designed for execution-aware link handling and attachment detonation stubs.

### What’s included
- FastAPI app with CORS and health endpoint
- Routers for `/api/ingest` and `/api/click`
- Service stubs for click proxy building and sandbox detonation
- Dockerfile and docker-compose with Postgres, Redis, and MinIO

### Quick start
1. Copy environment template and adjust as needed:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Build and run with Docker Compose:
   ```bash
   docker compose up --build
   ```
3. Visit health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

### Local dev without Docker
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend
```

### Next steps
- Implement click isolation proxy and screenshot pipeline
- Wire up S3 storage for uploaded artifacts
- Add database models and migrations
- Integrate static scanners (ClamAV, VT)
- Add SOC dashboard (React) and AI scoring pipelines


