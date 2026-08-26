# Guía de Desarrollo — SeniorVital

Plataforma de microservicios para el bienestar de adultos mayores. Backend en FastAPI + PostgreSQL + DuckDB + Ollama (IA local).

---

## 1. Arquitectura General

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Cliente   │────▶│  API Gateway │───▶ │  Microservicios  │
│ (React SPA) │     │   :8000      │     │  :8001 — :8006   │
└─────────────┘     └──────────────┘     └───────┬──────────┘
                                                 │
                          ┌────────────────── ───┼────────────────────┐
                          │                      │                    │
                    ┌─────▼──────┐         ┌─────▼─────┐        ┌─────▼─────┐
                    │ PostgreSQL │◀────────│  DuckDB   │        │  Ollama   │
                    │  :5432     │  replic.│  analít.  │        │  :11434   │
                    └────────────┘         └───────────┘        └───────────┘
```

| Capa | Tecnología | Puerto |
|------|-----------|--------|
| API Gateway | FastAPI (proxy inverso) | 8000 |
| Auth & Profile | FastAPI + JWT + bcrypt | 8001 |
| Catálogo Ejercicios | FastAPI + video upload | 8002 |
| Rutinas IA | FastAPI + Ollama | 8003 |
| Tracking | FastAPI + eventos | 8004 |
| Dashboard | FastAPI + DuckDB | 8005 |
| Notificaciones | FastAPI + Web Push | 8006 |
| Base datos | PostgreSQL 16+ | 5432 |
| IA Local | Ollama (phi3:mini) | 11434 |
| Analítica | DuckDB (embebido) | — |

**Comunicación síncrona**: REST vía API Gateway.
**Comunicación asíncrona**: Tabla `event_queue` en PostgreSQL (reemplaza a Redis/Celery).

---

## 2. Servicios — Endpoints

### 2.1 Auth Profile Service (`:8001`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/register` | Registro de usuario. Roles: `senior`, `caregiver`, `admin`. Profile validado contra `HealthProfile`. Password hasheado con bcrypt. |
| POST | `/auth/login` | Login. Devuelve JWT (HS256, 7 días). |
| GET | `/auth/me` | Perfil del usuario autenticado (token Bearer). |
| PUT | `/auth/profile` | Actualizar perfil (solo senior/admin). |
| POST | `/auth/link-caregiver` | Senior vincula un caregiver (máx. 3). |

**Modelos**:
- `RegisterRequest`: `{ email, password, role, profile? }`
- `LoginRequest`: `{ email, password }`
- `ProfileUpdate`: `{ profile }`
- `LinkCaregiverRequest`: `{ caregiver_email }`

### 2.2 Catalog Service (`:8002`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/catalog/exercises` | Listar ejercicios. Filtros: `level` (1–4), `name` (ILIKE). |
| POST | `/catalog/exercises` | Crear ejercicio. |
| GET | `/catalog/exercises/{id}` | Detalle de ejercicio. |
| PUT | `/catalog/exercises/{id}` | Actualizar ejercicio. |
| DELETE | `/catalog/exercises/{id}` | Eliminar ejercicio. |
| POST | `/catalog/exercises/{id}/video` | Subir video (max 50MB, video/*). |
| GET | `/storage/videos/{filename}` | Servir video almacenado. |

### 2.3 Routines AI Service (`:8003`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/routines/generate` | Generar rutina del día vía Ollama. Si `force=false` y ya existe, retorna la existente. Publica evento `rutina-generada`. Fallback a rutina por defecto si Ollama falla. |
| GET | `/routines/today` | Obtener rutina activa de hoy. Query: `user_id`. |

### 2.4 Tracking Service (`:8004`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/tracking/record` | Registrar un ejercicio. Publica `ejercicio-completado`. Si `rpe >= 8`, también publica `fatiga-alta`. Todo en una transacción. |
| POST | `/tracking/batch` | Registro por lote de múltiples ejercicios. |

### 2.5 Dashboard Service (`:8005`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/dashboard/progress/{user_id}` | Progreso semanal: calendario de reps, tendencia RPE, racha, sesiones. |
| GET | `/dashboard/projection/{user_id}` | Última proyección (insight) de la tabla `projections`. |
| GET | `/dashboard/insights/{user_id}` | Últimos 10 insights históricos. |

### 2.6 Notification Service (`:8006`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/notify/subscribe` | Guardar/actualizar suscripción Web Push (upsert). |
| POST | `/notify/send` | Enviar notificación push (background task). Elimina suscripción si 410 Gone. |

### 2.7 API Gateway (`:8000`)

Proxy inverso que rutea según el prefijo de la ruta:

| Prefijo | Destino |
|---------|---------|
| `/auth/` | `:8001` |
| `/catalog/` | `:8002` |
| `/routines/` | `:8003` |
| `/tracking/` | `:8004` |
| `/dashboard/` | `:8005` |
| `/notify/` | `:8006` |
| `/storage/` | `:8002` |

CORS habilitado para `http://localhost:3000`.

---

## 3. Base de Datos — PostgreSQL

### 3.1 Esquema de Tablas

```sql
-- Usuarios
users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('senior','caregiver','admin')),
    profile JSONB DEFAULT '{}',
    password TEXT NOT NULL,
    linked_senior_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
)

-- Tracking de ejercicios
tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    exercise_id TEXT NOT NULL,
    sets INT NOT NULL,
    reps INT NOT NULL,
    rpe INT CHECK (rpe BETWEEN 1 AND 10),
    felt_difficulty TEXT,
    completed_at TIMESTAMPTZ DEFAULT now()
)

-- Rutinas generadas
routines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    date DATE NOT NULL,
    exercises JSONB DEFAULT '[]',
    warmup JSONB DEFAULT '[]',
    active BOOLEAN DEFAULT true
)

-- Proyecciones / insights semanales
projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    week_start DATE NOT NULL,
    insight_text TEXT,
    estimated_level TEXT
)

-- Ejercicios del catálogo
exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    level INT NOT NULL,
    contraindications JSONB DEFAULT '[]',
    video_url TEXT
)

-- Cola de eventos asíncronos
event_queue (
    id BIGSERIAL PRIMARY KEY,
    stream_name TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
)

-- Suscripciones Web Push
push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    subscription JSONB NOT NULL
)

-- Hábitos (opcional)
habits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    habit_name TEXT NOT NULL,
    frequency TEXT,
    active BOOLEAN DEFAULT true
)
```

### 3.2 Tópicos de Eventos

| stream_name | Publicado por | Consumido por |
|-------------|--------------|---------------|
| `ejercicio-completado` | tracking-service | replicator.py |
| `fatiga-alta` | tracking-service | preventive_worker.py |
| `rutina-generada` | routines-ai-service | — |
| `inactividad-detectada` | daily_inactivity.py | — |
| `recomendacion-ajuste` | weekly_analysis.py | — |

---

## 4. Shared Library — `seniorvital_shared/`

### `db.py` — Pool de conexiones
- `init_pool(min_size, max_size, owner)` — Inicializa pool singleton con dueño.
- `get_pool()` — Retorna el pool (lo inicializa si es necesario).
- `close_pool(owner)` — Cierra el pool solo si el owner coincide.

### `models.py` — Modelos Pydantic
- `HealthProfile`: Edad (60–120), peso, altura, nivel fitness, metas, restricciones médicas (5 válidas), equipo, horario preferido.

### `events.py` — Publicación de eventos
- `publish_event(stream_name, payload)` — Inserta en `event_queue`.

---

## 5. Scripts & Workers

| Script | Tipo | Loop | Función |
|--------|------|------|---------|
| `replicator.py` | Consumidor | 1s | Lee `ejercicio-completado`, replica en DuckDB (`raw_events`, `weekly_progress`), marca `processed=true`. |
| `preventive_worker.py` | Consumidor | 2s | Lee `fatiga-alta`, loggea advertencia y notifica al caregiver vía notification-service. |
| `weekly_analysis.py` | Programado | 1 ejec. | Lee DuckDB, llama Ollama para generar insights, guarda en `projections`, publica `recomendacion-ajuste`. |
| `daily_inactivity.py` | Programado | 1 ejec. | Detecta seniors sin tracking en 4+ días, publica `inactividad-detectada`. |
| `start_all.ps1` / `.sh` | Arranque | — | Inicia los 7 servicios con uvicorn, guarda PIDs. |
| `stop_all.ps1` / `.sh` | Parada | — | Detiene servicios por PID y mata procesos residuales en puertos 8000–8006. |

---

## 6. Pruebas — Pytest

27 tests que cubren todos los criterios de aceptación.

### Configuración
- `pytest.ini`: `asyncio_mode = auto`
- `conftest.py`: Pool de BD compartido (`auto_init_pool`), limpieza automática entre tests (`cleanup`), carga dinámica de servicios (`load_service_app`).

### Tests por servicio

**Auth (5 tests):**
- `test_ac_auth_01_password_hashed` — Register exitoso.
- `test_ac_auth_02_invalid_role` — Rol inválido → 400.
- `test_ac_auth_03_caregiver_no_linked` — Caregiver sin senior vinculado.
- `test_ac_auth_04_max_3_caregivers` — Máx. 3 caregivers por senior.
- `test_ac_auth_05_caregiver_one_linked` — Caregiver solo un senior.

**Catalog (6 tests):**
- CRUD completo: create, list, get, update, delete + video upload.

**Dashboard (3 tests):**
- Progress user not found → 404.
- Projection null → 200 con `null`.
- Insights empty → 200 con `[]`.

**Notifications (3 tests):**
- Subscribe, subscribe overwrite, send notification.

**Persistence (4 tests):**
- HealthProfile valid, invalid restriction, caregiver linked senior, event_queue insert.

**Routines (3 tests):**
- Generate user not found, get today not found, generate twice returns existing.

**Tracking (3 tests):**
- Record exercise, record high fatigue, batch record.

### Ejecución
```powershell
pytest tests/ -v          # Todos los tests
pytest tests/test_auth.py -v  # Solo auth
pytest tests/ -k "track"      # Por palabra clave
```

---

## 7. Configuración de Entorno

`.env.example`:
```env
DATABASE_URL=postgresql://postgres:9739185@localhost:5432/seniorvital
OLLAMA_URL=http://localhost:11434
JWT_SECRET=super-secret-key-change-in-production
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=admin@seniorvital.com
```

---

## 8. Dependencias

### Sistema
- Python 3.12+
- PostgreSQL 16+ (puerto 5432)
- Ollama (puerto 11434) con modelo `phi3:mini`

### Python (compartido)
```
fastapi, uvicorn, asyncpg, passlib[bcrypt], python-jose[cryptography],
pydantic[email], python-dotenv, httpx, python-multipart, aiofiles,
duckdb, pywebpush, pytest, pytest-asyncio
```

---

## 9. Comandos Rápidos

```powershell
# Instalar todo
pip install -r requirements.txt

# Iniciar BD (una vez)
# Ejecutar init_db.sql en pgAdmin
# Luego scripts/migrations.sql

# Arrancar todo
.\scripts\start_all.ps1

# Tests
pytest tests/ -v

# Servicio individual
cd auth-profile-service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Detener todo
.\scripts\stop_all.ps1
```

---

## 10. Estructura del Proyecto

```
E:\SeniorVital\
├── auth-profile-service/   # Auth + perfiles (8001)
├── catalog-service/        # Catálogo ejercicios + videos (8002)
├── routines-ai-service/    # Rutinas con IA (8003)
├── tracking-service/       # Tracking ejercicios (8004)
├── dashboard-service/      # Dashboard analítico (8005)
├── notification-service/   # Notificaciones push (8006)
├── gateway/                # API Gateway (8000)
├── seniorvital_shared/     # Librería compartida
├── scripts/                # Workers + automatización
│   ├── replicator.py       # Replicación a DuckDB
│   ├── preventive_worker.py# Alerta fatiga alta
│   ├── weekly_analysis.py  # Análisis semanal IA
│   ├── daily_inactivity.py # Detección inactividad
│   ├── migrations.sql      # Migraciones BD
│   ├── start_all.ps1/.sh   # Arranque servicios
│   └── stop_all.ps1/.sh    # Parada servicios
├── tests/                  # Suite de pruebas (27 tests)
├── storage/                # Archivos subidos
│   ├── videos/
│   └── progress-photos/
├── logs/                   # Logs de servicios
├── .env.example            # Variables de entorno
├── SDD.md                  # Documento de diseño
├── GUIA_DESARROLLO.md      # Esta guía
└── AGENTS.md               # Config OpenCode
```

---

## 11. Flujos Principales

### Registro y Login
```
Cliente ──POST /auth/register──▶ Auth Service ──bcrypt hash──▶ PostgreSQL
Cliente ──POST /auth/login─────▶ Auth Service ──verify──────▶ JWT token
```

### Tracking con Eventos
```
Cliente ──POST /tracking/record──▶ Tracking Service
                                      │
                          ┌───────────┼────────────┐
                          ▼           ▼            ▼
                     PostgreSQL   event_queue   event_queue
                     (tracking)   (ejercicio-   (fatiga-alta
                                  completado)    si rpe>=8)
```

### Replicación a DuckDB
```
event_queue ──poll──▶ replicator.py ──insert──▶ DuckDB
(ejercicio-completado)              (raw_events, weekly_progress)
```

### Generación de Rutina IA
```
Cliente ──POST /routines/generate──▶ Routines Service
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                     PostgreSQL      Ollama (phi3:mini)  event_queue
                     (perfil user)   (prompt → rutina)  (rutina-generada)
```

---

## 12. Notas de Desarrollo

- **Pool de conexiones**: Singleton con sistema de `owner` para que tests y servicios compartan el pool sin cierres accidentales.
- **Tipos datetime**: asyncpg requiere objetos `datetime` nativos (offset-naive) para columnas `TIMESTAMP`. No usar strings ISO.
- **Archivos de video**: Almacenados en `storage/videos/` con nombre UUID. Servidos por FastAPI con `FileResponse`.
- **Tests**: Usan `ASGITransport` (httpx) para pruebas sin servidor real. Cada test limpia la BD automáticamente.
- **Eventos asíncronos**: No se usa Redis/Celery. La tabla `event_queue` sirve como buffer. Workers pollan con intervalos fijos.
