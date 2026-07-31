# SeniorVital

Plataforma Inteligente de Bienestar para Adultos Mayores.

## Architecture

Microservicios backend con FastAPI, PostgreSQL, DuckDB y Ollama (IA local).

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Proxy/CORS router |
| Auth Profile | 8001 | User registration, login, profiles |
| Catalog | 8002 | Exercise catalog & video storage |
| Routines AI | 8003 | AI routine generation via Ollama |
| Tracking | 8004 | Exercise tracking & event publishing |
| Dashboard | 8005 | Progress analytics & projections |
| Notification | 8006 | Web Push notifications |

## Prerequisites

- Python 3.12+
- PostgreSQL 16+ (running on port 5432)
- Ollama (running on port 11434, with `phi3:mini` model)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo> seniorvital
   cd seniorvital
   ```

2. **Install dependencies**
   ```bash
   pip install -r auth-profile-service/requirements.txt
   pip install -r catalog-service/requirements.txt
   pip install -r routines-ai-service/requirements.txt
   pip install -r tracking-service/requirements.txt
   pip install -r dashboard-service/requirements.txt
   pip install -r notification-service/requirements.txt
   pip install -r gateway/requirements.txt
   pip install duckdb pywebpush pytest httpx aiofiles
   ```

3. **Initialize the database**
   - Open pgAdmin and execute `init_db.sql` against the `seniorvital` database.
   - Then execute `scripts/migrations.sql` to add the password column and push_subscriptions table.

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings if needed
   ```

5. **Pull Ollama model**
   ```bash
   ollama pull phi3:mini
   ```

## Running

### Start all services
```powershell
# PowerShell
.\scripts\start_all.ps1
```
```bash
# Git Bash / WSL
bash scripts/start_all.sh
```

### Stop all services
```powershell
.\scripts\stop_all.ps1
```
```bash
bash scripts/stop_all.sh
```

### Start a single service
```bash
cd auth-profile-service
uvicorn main:app --port 8001 --reload
```

## Testing

```bash
pytest tests/ -v
```

## API Documentation

Each service exposes interactive docs at `/docs`:
- Gateway: http://localhost:8000/docs
- Auth Profile: http://localhost:8001/docs
- Catalog: http://localhost:8002/docs
- Routines AI: http://localhost:8003/docs
- Tracking: http://localhost:8004/docs
- Dashboard: http://localhost:8005/docs
- Notification: http://localhost:8006/docs

## Background Workers

These run as independent processes:
- `replicator.py` - Replicates events from PostgreSQL to DuckDB (every 1s)
- `preventive_worker.py` - Handles high-fatigue events (every 2s)
- `weekly_analysis.py` - Runs weekly AI analysis (manual/scheduled)
- `daily_inactivity.py` - Detects inactive users (daily)
