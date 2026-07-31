# AGENTS.md - SeniorVital Configuration for OpenCode

## Project Overview
SeniorVital is a microservices-based backend platform for elderly wellness management.
It uses FastAPI, PostgreSQL, DuckDB, and Ollama (local AI).

## Directory Structure
```
seniorvital/
├── auth-profile-service/   # User auth & profile management (port 8001)
├── catalog-service/        # Exercise catalog & video storage (port 8002)
├── routines-ai-service/    # AI routine generation via Ollama (port 8003)
├── tracking-service/       # Exercise tracking & event publishing (port 8004)
├── dashboard-service/      # Progress & analytics queries (port 8005)
├── notification-service/   # Web Push notifications (port 8006)
├── gateway/                # API Gateway / proxy (port 8000)
├── scripts/                # Automation & background workers
│   ├── start_all.sh        # Start all services
│   ├── stop_all.sh         # Stop all services
│   ├── replicator.py       # DB event -> DuckDB replication
│   ├── preventive_worker.py# High-fatigue event handler
│   ├── weekly_analysis.py  # Weekly AI analysis
│   └── daily_inactivity.py # Inactivity detection
├── seniorvital_shared/     # Shared library (db, models, events)
├── storage/                # Local file storage
│   ├── videos/
│   └── progress-photos/
├── tests/                  # Pytest test suite
├── logs/                   # Service logs & PID files
└── SDD.md                  # System Design Document (source of truth)
```

## Commands
- **Install**: `pip install -r requirements.txt` (in each service dir + root)
- **Init DB**: Execute `init_db.sql` in pgAdmin (already done)
- **Run migrations**: Execute `scripts/migrations.sql` in pgAdmin
- **Start all**: `.\scripts\start_all.ps1` (PowerShell) or `bash scripts/start_all.sh`
- **Stop all**: `.\scripts\stop_all.ps1` (PowerShell) or `bash scripts/stop_all.sh`
- **Tests**: `pytest tests/ -v`
- **Single service**: `cd <service> && uvicorn main:app --port <port> --reload`

## Dependencies (Python 3.12+)
- PostgreSQL (port 5432) - database
- Ollama (port 11434) - local AI with phi3:mini model
- Python packages: fastapi, uvicorn, asyncpg, httpx, duckdb, pywebpush, passlib, python-jose, pydantic, pytest

## Architecture
- Synchronous: REST via API Gateway (port 8000) -> microservices
- Asynchronous: PostgreSQL event_queue table (instead of Redis)
- Analytics: DuckDB (embedded, file-based)
- Auth: JWT tokens via FastAPI Users style (bcrypt passwords)
