# Arquitectura de SeniorVital — Mapa Completo del Proyecto

Sistema backend de microservicios para el bienestar de adultos mayores.
Stack: FastAPI, PostgreSQL asíncrono (asyncpg + JSONB), autenticación JWT, IA local con Ollama.

---

## 1. Árbol de Directorios

```
E:\SeniorVital\
│
├── .env                          # Variables de entorno (local, excluido de VCS)
├── .env.example                  # Plantilla de variables de entorno
├── AGENTS.md                     # Configuración para OpenCode
├── ARQUITECTURA.md               # Este documento
├── GUIA_DESARROLLO.md            # Guía de desarrollo
├── README.md                     # Documentación principal del proyecto
├── REQUISITOS_FUNCIONALES.md     # Lista de requisitos por microservicio
├── SDD.md                        # System Design Document (fuente de verdad)
├── init_db.sql                   # Script de inicialización del esquema PostgreSQL
├── pytest.ini                    # Configuración de pytest
├── requirements.txt              # Dependencias globales del proyecto
│
├───auth-profile-service/         # [8001] Autenticación y perfiles
│       main.py                   #   Aplicación FastAPI completa
│       requirements.txt          #   Dependencias del servicio
│
├───catalog-service/              # [8002] Catálogo de ejercicios y videos
│       main.py
│       requirements.txt
│
├───dashboard-service/            # [8005] Dashboard y analítica
│       main.py
│       requirements.txt
│
├───gateway/                      # [8000] API Gateway (proxy inverso)
│       main.py
│       requirements.txt
│
├───notification-service/         # [8006] Notificaciones Web Push
│       main.py
│       requirements.txt
│
├───routines-ai-service/          # [8003] Generación de rutinas con IA
│       main.py
│       requirements.txt
│
├───tracking-service/             # [8004] Tracking de ejercicios y eventos
│       main.py
│       requirements.txt
│
├───scripts/                      # Automatización y workers background
│       daily_inactivity.py       #   Detección de inactividad (>4 días)
│       migrations.sql            #   Migraciones de esquema BD
│       preventive_worker.py      #   Consumidor de eventos fatiga-alta
│       replicator.py             #   Replicación PostgreSQL → DuckDB
│       start_all.ps1             #   Inicio de servicios (PowerShell)
│       start_all.sh              #   Inicio de servicios (Bash)
│       stop_all.ps1              #   Parada de servicios (PowerShell)
│       stop_all.sh               #   Parada de servicios (Bash)
│       weekly_analysis.py        #   Análisis semanal con IA
│
├───seniorvital_shared/           # Librería compartida entre servicios
│       __init__.py               #   Exportaciones públicas
│       db.py                     #   Pool de conexiones PostgreSQL
│       events.py                 #   Publicación de eventos asíncronos
│       models.py                 #   Modelos Pydantic (HealthProfile)
│
├───storage/                      # Almacenamiento local de archivos
│   ├───progress-photos/          #   Fotos de progreso (vacío)
│   └───videos/                   #   Videos de ejercicios subidos
│           *.mp4                 #   8 archivos de video
│
├───tests/                        # Suite de pruebas pytest
│       __init__.py               #   Paquete de tests
│       conftest.py               #   Fixtures compartidos
│       test_auth.py              #   Tests de autenticación (5)
│       test_catalog.py           #   Tests de catálogo (6)
│       test_dashboard.py         #   Tests de dashboard (3)
│       test_db_conn.py           #   Script de verificación BD
│       test_notification.py      #   Tests de notificaciones (3)
│       test_persistence.py       #   Tests de persistencia (4)
│       test_routines.py          #   Tests de rutinas IA (3)
│       test_tracking.py          #   Tests de tracking (3)
│       get_pg_credential.py      #   Helper: credenciales PostgreSQL
│       get_pg_credential2.py     #   Helper alternativo
│       get_pgpass.py             #   Helper: pgpass
│       get_windows_credential.py #   Helper: Windows Credential Manager
│
└───logs/                         # Logs de servicios (creado en tiempo de ejecución)
```

---

## 2. Descripción de Carpetas

### 2.1 `auth-profile-service/` — Autenticación y Perfiles (puerto 8001)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Registro, login, gestión de perfiles, roles y vinculación cuidador-senior |
| **Tecnologías clave** | FastAPI, passlib[bcrypt], python-jose, Pydantic[EmailStr] |
| **Independencia** | Servicio independiente, comparte pool de BD vía `seniorvital_shared` |

**Archivos:**
- `main.py` — Aplicación FastAPI completa: modelos Pydantic (`RegisterRequest`, `LoginRequest`, `ProfileUpdate`, `LinkCaregiverRequest`), endpoints REST, lógica de bcrypt y JWT, ciclo de vida del pool.
- `requirements.txt` — fastapi, uvicorn, asyncpg, passlib[bcrypt], python-jose[cryptography], pydantic[email], python-dotenv, httpx.

### 2.2 `catalog-service/` — Catálogo de Ejercicios (puerto 8002)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | CRUD de ejercicios, subida y servicio de videos |
| **Tecnologías clave** | FastAPI, aiofiles, python-multipart, almacenamiento local |
| **Independencia** | Servicio independiente; sirve archivos estáticos vía `/storage/videos/` |

**Archivos:**
- `main.py` — CRUD completo (`GET/POST/PUT/DELETE /catalog/exercises`), subida de video (`POST /catalog/exercises/{id}/video`), servidor de archivos (`GET /storage/videos/{filename}`).
- `requirements.txt` — fastapi, uvicorn, asyncpg, pydantic, python-dotenv, python-multipart, aiofiles, httpx.

### 2.3 `routines-ai-service/` — Rutinas con IA (puerto 8003)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Generar rutinas de ejercicio personalizadas usando Ollama |
| **Tecnologías clave** | FastAPI, httpx (cliente Ollama), phi3:mini |
| **Independencia** | Servicio independiente; requiere Ollama en `localhost:11434` |

**Archivos:**
- `main.py` — Endpoint `POST /routines/generate` (genera rutina vía Ollama con fallback a rutina por defecto), endpoint `GET /routines/today` (consulta rutina activa), función `call_ollama()`, función `build_prompt()`.
- `requirements.txt` — fastapi, uvicorn, asyncpg, pydantic, python-dotenv, httpx.

### 2.4 `tracking-service/` — Tracking de Ejercicios (puerto 8004)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Registrar sesiones de ejercicio, publicar eventos asíncronos |
| **Tecnologías clave** | FastAPI, asyncpg, event_queue (PostgreSQL) |
| **Independencia** | Servicio independiente; publica eventos en tabla compartida |

**Archivos:**
- `main.py` — Endpoint `POST /tracking/record` (registro individual con publicación de eventos `ejercicio-completado` y `fatiga-alta`), endpoint `POST /tracking/batch` (registro por lote en una transacción), modelos `TrackEntry` y `BatchTrackRequest`.
- `requirements.txt` — fastapi, uvicorn, asyncpg, pydantic, python-dotenv, httpx.

### 2.5 `dashboard-service/` — Dashboard y Analítica (puerto 8005)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Consultas agregadas de progreso, proyecciones e insights |
| **Tecnologías clave** | FastAPI, asyncpg, DuckDB |
| **Independencia** | Servicio independiente; lee de PostgreSQL y DuckDB |

**Archivos:**
- `main.py` — Endpoint `GET /dashboard/progress/{user_id}` (calendario semanal, tendencia RPE, racha, sesiones), `GET /dashboard/projection/{user_id}` (última proyección), `GET /dashboard/insights/{user_id}` (historial de insights).
- `requirements.txt` — fastapi, uvicorn, asyncpg, pydantic, python-dotenv, duckdb, httpx.

### 2.6 `notification-service/` — Notificaciones Push (puerto 8006)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Gestionar suscripciones Web Push y enviar notificaciones |
| **Tecnologías clave** | FastAPI, pywebpush, VAPID, BackgroundTasks |
| **Independencia** | Servicio independiente; tabla `push_subscriptions` propia |

**Archivos:**
- `main.py` — Endpoint `POST /notify/subscribe` (guardar/sobrescribir suscripción con upsert), endpoint `POST /notify/send` (encolar envío push como background task), función `send_push_notification()` con manejo de errores 410 Gone.
- `requirements.txt` — fastapi, uvicorn, asyncpg, pydantic, python-dotenv, pywebpush, httpx.

### 2.7 `gateway/` — API Gateway (puerto 8000)

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Proxy inverso que rutea peticiones al microservicio correcto |
| **Tecnologías clave** | FastAPI, httpx, CORSMiddleware |
| **Independencia** | Servicio frontal único; punto de entrada para todos los clientes |

**Archivos:**
- `main.py` — Mapa de rutas (`ROUTES`), función `proxy_request()` que reenvía la petición HTTP al microservicio destino, ruta comodín `/{path:path}` que captura todas las peticiones, configuración CORS para `localhost:3000`.
- `requirements.txt` — fastapi, uvicorn, httpx, pydantic, python-dotenv.

### 2.8 `seniorvital_shared/` — Librería Compartida

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Pool de conexiones PostgreSQL, modelos de dominio, publicación de eventos |
| **Uso** | Paquete Python instalado por todos los servicios via `sys.path.insert` |
| **Dependencia clave** | asyncpg, pydantic |

**Archivos:**
- `__init__.py` — Exporta `get_pool`, `init_pool`, `close_pool`, `HealthProfile`, `publish_event`.
- `db.py` — Pool singleton con sistema de `owner` para evitar cierres prematuros. Funciones: `init_pool(min_size, max_size, owner)`, `close_pool(owner)`, `get_pool()`.
- `models.py` — `HealthProfile` (Pydantic): edad, peso, altura, nivel fitness, metas, restricciones médicas (5 valores permitidos), equipo.
- `events.py` — `publish_event(stream_name, payload)`: inserta en `event_queue`.

### 2.9 `scripts/` — Automatización y Workers

| Atributo | Valor |
|----------|-------|
| **Responsabilidad** | Workers background, scripts de inicio/parada, migraciones |
| **Ejecución** | Procesos independientes (workers bucle infinito) o programados (cron) |

**Archivos:**

| Archivo | Tipo | Función |
|---------|------|---------|
| `replicator.py` | Worker (loop 1s) | Lee `ejercicio-completado` de `event_queue`, replica en DuckDB (`raw_events`, `weekly_progress`), marca `processed=true`. |
| `preventive_worker.py` | Worker (loop 2s) | Lee `fatiga-alta` de `event_queue`, loggea alerta, notifica vía notification-service. |
| `weekly_analysis.py` | Programado (lunes 2AM) | Lee DuckDB, llama Ollama para insights, guarda en `projections`, publica `recomendacion-ajuste`. |
| `daily_inactivity.py` | Programado (diario) | Detecta seniors sin tracking en 4+ días, publica `inactividad-detectada`. |
| `start_all.ps1` | Script PowerShell | Inicia los 7 servicios con uvicorn, guarda PIDs. |
| `start_all.sh` | Script Bash | Equivalente a start_all.ps1. |
| `stop_all.ps1` | Script PowerShell | Detiene servicios por PID, limpia puertos 8000-8006. |
| `stop_all.sh` | Script Bash | Equivalente a stop_all.ps1. |
| `migrations.sql` | SQL | ADD COLUMN password en users, CREATE TABLE push_subscriptions. |

### 2.10 `tests/` — Suite de Pruebas

| Atributo | Valor |
|----------|-------|
| **Framework** | pytest 9.x con pytest-asyncio (asyncio_mode=auto) |
| **Cobertura** | 27 tests, 8 archivos de test |
| **Infraestructura** | Pool compartido `auto_init_pool`, limpieza automática `cleanup`, carga dinámica `load_service_app` |

**Archivos:**

| Archivo | Tests | Criterios de Aceptación |
|---------|-------|------------------------|
| `conftest.py` | Fixtures | — |
| `test_auth.py` | 5 | AC-AUTH-01 al 05 |
| `test_catalog.py` | 6 | CRUD + video |
| `test_dashboard.py` | 3 | Progreso, proyección, insights |
| `test_notification.py` | 3 | AC-NOT-01, AC-NOT-02 |
| `test_persistence.py` | 4 | AC-PERS-01, 02, 03 |
| `test_routines.py` | 3 | Rutinas IA |
| `test_tracking.py` | 3 | Tracking individual, fatiga alta, lote |

Helpers de credenciales: `get_pg_credential.py`, `get_pg_credential2.py`, `get_pgpass.py`, `get_windows_credential.py`.

### 2.11 `storage/` — Almacenamiento Local

| Subcarpeta | Propósito |
|------------|-----------|
| `videos/` | Videos de ejercicios subidos vía catalog-service (archivos .mp4 con nombre UUID) |
| `progress-photos/` | Fotos de progreso (reservado para uso futuro) |

### 2.12 `logs/` — Logs de Servicios

Creado en tiempo de ejecución por `start_all.ps1`/`start_all.sh`. Contiene archivos `.pid` y logs de cada servicio.

### 2.13 Archivos de Configuración Raíz

| Archivo | Propósito |
|---------|-----------|
| `.env` | Variables de entorno locales (no versionado) |
| `.env.example` | Plantilla con valores por defecto |
| `.pytest.ini` | `asyncio_mode = auto`, `testpaths = tests` |
| `requirements.txt` | Dependencias globales del proyecto |
| `init_db.sql` | Esquema completo PostgreSQL (8 tablas, índices) |
| `SDD.md` | System Design Document — fuente de verdad del diseño |
| `AGENTS.md` | Configuración para OpenCode (asistente de desarrollo) |

---

## 3. Descripción Detallada de Cada Archivo

### 3.1 `seniorvital_shared/db.py`

**Funcionalidad:** Pool de conexiones a PostgreSQL singleton con sistema de propietario (owner). Tres funciones asíncronas:

- `init_pool(min_size, max_size, owner)` — Crea el pool si no existe, asigna un owner.
- `close_pool(owner)` — Cierra el pool solo si el owner coincide (protección contra cierres accidentales entre servicios y tests).
- `get_pool()` — Retorna el pool existente o lo inicializa con valores por defecto.

**Uso:** Fundamental para todos los servicios. Cada servicio llama a `init_pool(owner="...")` en su `lifespan` y a `close_pool(owner="...")` al terminar.

**Conexiones:**
- Importado por: todos los microservicios, `tests/conftest.py`, `tests/test_routines.py`, `tests/test_tracking.py`.
- Dependencia: `asyncpg`, `os`.
- Variable de entorno: `DATABASE_URL`.

### 3.2 `seniorvital_shared/models.py`

**Funcionalidad:** Modelo `HealthProfile` (Pydantic BaseModel) que valida el perfil de salud de un adulto mayor:

| Campo | Tipo | Validación |
|-------|------|------------|
| `age` | int | 60 ≤ age ≤ 120 |
| `weight_kg` | float | 30 ≤ weight ≤ 200 |
| `height_cm` | float | 100 ≤ height ≤ 250 |
| `fitness_level` | str | `^(principiante\|intermedio\|avanzado)$` |
| `goals` | List[str] | min_length=1 |
| `medical_restrictions` | List[str] | Solo valores permitidos (5) |
| `equipment` | List[str] | defaults to [] |
| `preferred_schedule` | Optional[str] | Sin restricción |

**Valores permitidos para `medical_restrictions`:**
`artrosis_rodilla`, `osteoporosis`, `hipertensión`, `dolor_articular`, `prótesis`.

**Conexiones:** Usado por `auth-profile-service` (validación en register/profile update) y `tests/test_persistence.py`.

### 3.3 `seniorvital_shared/events.py`

**Funcionalidad:** Publicación de eventos asíncronos. La función `publish_event(stream_name, payload)` inserta una fila en la tabla `event_queue` con el stream name y el payload serializado a JSON.

**Conexiones:** Usado por `routines-ai-service`. Depende de `db.py` para obtener el pool.

### 3.4 `seniorvital_shared/__init__.py`

**Funcionalidad:** Exporta los símbolos públicos del paquete compartido: `get_pool`, `init_pool`, `close_pool`, `HealthProfile`, `publish_event`.

### 3.5 `auth-profile-service/main.py`

**Funcionalidad:** Microservicio completo de autenticación y perfiles. Contiene:

**Constantes:**
- `JWT_SECRET`: desde variable de entorno, con fallback.
- `JWT_ALG = "HS256"`, `JWT_EXPIRY = timedelta(days=7)`.
- `security = HTTPBearer()`: esquema de seguridad Bearer token.

**Funciones auxiliares:**

| Función | Descripción |
|---------|-------------|
| `create_token(user_id)` | Genera JWT con sub=user_id, exp=now+7d, firmado con HS256 |
| `verify_token(credentials)` | Decodifica y valida JWT; raise 401 si inválido |
| `get_current_user(payload)` | Obtiene registro completo de BD desde el sub del token |
| `lifespan(app)` | Inicializa pool, agrega columna password si no existe, cierra pool al final |

**Modelos Pydantic:**

| Clase | Campos | Uso |
|-------|--------|-----|
| `RegisterRequest` | email: EmailStr, password: str, role: str="senior", profile: Optional[dict] | POST /auth/register |
| `LoginRequest` | email: EmailStr, password: str | POST /auth/login |
| `ProfileUpdate` | profile: dict | PUT /auth/profile |
| `LinkCaregiverRequest` | caregiver_email: EmailStr | POST /auth/link-caregiver |

**Endpoints REST:**

| Método | Ruta | Función | Validaciones Clave |
|--------|------|---------|-------------------|
| POST | `/auth/register` | `register()` | role en (senior,caregiver,admin), email único, profile válido, bcrypt hash |
| POST | `/auth/login` | `login()` | bcrypt verify, devuelve JWT |
| GET | `/auth/me` | `get_me()` | Requiere token Bearer |
| PUT | `/auth/profile` | `update_profile()` | Solo senior/admin, HealthProfile validation |
| POST | `/auth/link-caregiver` | `link_caregiver()` | Solo senior, máx 3 caregivers, caregiver único |

**Conexiones:**
- `seniorvital_shared`: `get_pool`, `init_pool`, `close_pool`, `HealthProfile`
- `passlib.hash.bcrypt`: hashing y verificación de contraseñas
- `jose.jwt`, `jose.JWTError`: creación y verificación de JWT
- `fastapi.security.HTTPBearer`: extracción de tokens Bearer

### 3.6 `catalog-service/main.py`

**Funcionalidad:** CRUD de ejercicios + subida y servicio de videos.

**Modelos:**
- `ExerciseCreate`: name, level (1-4), contraindications[], video_url?
- `ExerciseUpdate`: todos los campos opcionales

**Endpoints:**

| Método | Ruta | Función |
|--------|------|---------|
| GET | `/catalog/exercises` | `list_exercises()` — filtros por level y name (ILIKE) |
| POST | `/catalog/exercises` | `create_exercise()` — valida level 1-4, HTTP 201 |
| GET | `/catalog/exercises/{id}` | `get_exercise()` — HTTP 404 si no existe |
| PUT | `/catalog/exercises/{id}` | `update_exercise()` — actualización parcial |
| DELETE | `/catalog/exercises/{id}` | `delete_exercise()` — HTTP 404 si no existe |
| POST | `/catalog/exercises/{id}/video` | `upload_video()` — MP4, max 50MB, guarda en storage/videos/ |
| GET | `/storage/videos/{filename}` | `serve_video()` — FileResponse video/mp4 |

**Conexiones:**
- `seniorvital_shared`: pool de BD
- `aiofiles`: escritura asíncrona de archivos de video
- `uuid`: generación de nombres únicos para videos
- Almacenamiento: `storage/videos/` en sistema de archivos local

### 3.7 `routines-ai-service/main.py`

**Funcionalidad:** Generación de rutinas personalizadas usando Ollama (phi3:mini).

**Componentes clave:**

| Elemento | Descripción |
|----------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` (configurable vía env) |
| `OLLAMA_MODEL` | `phi3:mini` |
| `DEFAULT_ROUTINE` | Rutina de fallback: 3 ejercicios + 1 warmup |
| `GenerateRequest` | user_id + force (bool) |
| `call_ollama(prompt)` | Cliente HTTP asíncrono a Ollama API `/api/generate` |
| `build_prompt(profile, safe_exercises)` | Construye prompt con perfil + ejercicios seguros |

**Flujo de `POST /routines/generate`:**
1. Obtener usuario de BD → 404 si no existe
2. Si `force=false` y ya hay rutina activa para hoy, retornarla
3. Parsear profile (JSON string → dict)
4. Filtrar ejercicios del catálogo excluyendo contraindicados
5. Llamar a Ollama con el prompt construido
6. Si Ollama falla, usar `DEFAULT_ROUTINE`
7. Insertar en tabla `routines`
8. Publicar evento `rutina-generada`
9. Retornar rutina generada

**Conexiones:**
- Ollama: `POST /api/generate` con httpx
- `seniorvital_shared`: pool de BD + `publish_event`
- Tablas: `users`, `exercises`, `routines`, `event_queue`

### 3.8 `tracking-service/main.py`

**Funcionalidad:** Registro de sesiones de ejercicio con publicación de eventos.

**Modelos:**
- `TrackEntry`: user_id, exercise_id, sets, reps, rpe?, felt_difficulty?, completed_at?
- `BatchTrackRequest`: entries (lista de TrackEntry)

**Flujo de `POST /tracking/record`:**
1. Insertar en tabla `tracking`
2. Publicar evento `ejercicio-completado` con payload completo
3. Si rpe >= 8, publicar evento `fatiga-alta`
4. Todo en una sola transacción PostgreSQL

**Flujo de `POST /tracking/batch`:** Mismo comportamiento, iterando sobre cada entrada.

**Conexiones:**
- `seniorvital_shared`: pool de BD
- Tablas: `tracking`, `event_queue`
- Foreign key: `tracking.user_id → users.id`

### 3.9 `dashboard-service/main.py`

**Funcionalidad:** Consultas de progreso, proyecciones e insights.

**Endpoints:**

| Ruta | Función | Lógica |
|------|---------|--------|
| `GET /dashboard/progress/{user_id}` | `get_progress()` | Calendario semanal de reps, tendencia RPE, racha de días consecutivos, total sesiones semanales |
| `GET /dashboard/projection/{user_id}` | `get_projection()` | Última fila de `projections` ordenada por week_start DESC |
| `GET /dashboard/insights/{user_id}` | `get_insights()` | Últimas 10 filas de `projections` |

**Cálculo de racha:** Itera hacia atrás desde hoy contando días con al menos un registro en tracking.

**Conexiones:** `seniorvital_shared` (pool), tablas `users`, `tracking`, `projections`.

### 3.10 `notification-service/main.py`

**Funcionalidad:** Suscripción y envío de notificaciones Web Push.

**Modelos:**
- `SubscribeRequest`: user_id, subscription (dict con endpoint, keys)
- `SendNotificationRequest`: user_id, title, body

**Componentes:**

| Elemento | Descripción |
|----------|-------------|
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | Claves VAPID para Web Push |
| `VAPID_CLAIM_EMAIL` | Email para el claim sub de VAPID |
| `subscribe()` | Upsert en `push_subscriptions` |
| `send_push_notification()` | Función asíncrona: busca suscripción, envía vía pywebpush, elimina si 410 Gone |
| `send_notification()` | Encola la función anterior como BackgroundTask de FastAPI |

**Conexiones:**
- `pywebpush.webpush`: envío de notificaciones push
- `seniorvital_shared`: pool de BD
- Tabla `push_subscriptions` (creada automáticamente en lifespan)

### 3.11 `gateway/main.py`

**Funcionalidad:** Proxy inverso que reenvía peticiones al microservicio correcto según el prefijo de la ruta.

**Mapa de rutas:**

| Prefijo | Destino |
|---------|---------|
| `/auth/` | `http://localhost:8001` |
| `/catalog/` | `http://localhost:8002` |
| `/routines/` | `http://localhost:8003` |
| `/tracking/` | `http://localhost:8004` |
| `/dashboard/` | `http://localhost:8005` |
| `/notify/` | `http://localhost:8006` |
| `/storage/` | `http://localhost:8002` |

**Flujo de `proxy_request()`:**
1. Identificar prefijo en ROUTES
2. Construir URL destino
3. Reenviar método, body, headers y query params
4. Devolver respuesta exacta del microservicio
5. HTTP 502 si el servicio no responde o no hay ruta

**Conexiones:** `httpx.AsyncClient` para reenvío HTTP, `CORSMiddleware` para CORS.

### 3.12 `scripts/replicator.py`

**Funcionalidad:** Bucle infinito (1s de intervalo) que replica eventos `ejercicio-completado` desde PostgreSQL a DuckDB.

**Flujo:**
1. `ensure_duckdb_schema()`: crea tablas `raw_events` y `weekly_progress` en DuckDB
2. `process_events()`: consulta `event_queue` (stream_name='ejercicio-completado', processed=FALSE, LIMIT 100)
3. Por cada evento: inserta en `raw_events`, actualiza `weekly_progress` (INSERT OR REPLACE), marca `processed=TRUE`
4. Si DuckDB falla, no marca como procesado (reintento)

**Conexiones:** asyncpg (PostgreSQL), duckdb, `seniorvital_analytics.duckdb` (archivo).

### 3.13 `scripts/preventive_worker.py`

**Funcionalidad:** Bucle infinito (2s de intervalo) que procesa eventos `fatiga-alta`.

**Flujo:**
1. Consulta `event_queue` (stream_name='fatiga-alta', processed=FALSE, LIMIT 50)
2. Por cada evento: loggea alerta, intenta notificar vía `POST http://localhost:8006/notify/send`
3. Marca como procesado

### 3.14 `scripts/weekly_analysis.py`

**Funcionalidad:** Análisis semanal (ejecución única, diseñado para cron los lunes 2AM).

**Flujo:**
1. Conecta a DuckDB, obtiene usuarios con datos en `weekly_progress`
2. Para cada usuario: calcula promedio semanal, llama Ollama para generar insight
3. Guarda en `projections` (PostgreSQL)
4. Publica evento `recomendacion-ajuste`

**Conexiones:** asyncpg (PostgreSQL), duckdb (DuckDB), httpx (Ollama).

### 3.15 `scripts/daily_inactivity.py`

**Funcionalidad:** Detección diaria de inactividad (ejecución única).

**Flujo:**
1. Busca seniors sin registros en `tracking` en los últimos 4 días
2. Por cada inactivo: publica evento `inactividad-detectada`

### 3.16 `tests/conftest.py`

**Funcionalidad:** Configuración compartida de pytest.

| Elemento | Descripción |
|----------|-------------|
| `load_service_app(name)` | Carga dinámicamente el módulo main.py de un servicio y retorna `app` |
| `auto_init_pool` (fixture autouse) | Inicializa pool BD con owner="test" antes de cada test |
| `cleanup` (fixture autouse) | Limpia todas las tablas después de cada test |

**Conexiones:** Usado por todos los test files via `from .conftest import load_service_app`.

---

## 4. Mapa de Relaciones y Vínculos

### 4.1 Diagrama de Arquitectura General

```
┌──────────────┐     ┌──────────────────────────────────────────────────────┐
│   Cliente    │     │                  API Gateway (:8000)                  │
│  (React SPA) │────▶│  Proxy inverso con ruteo por prefijo de ruta         │
└──────────────┘     └──┬──────────┬──────────┬──────────┬──────────┬───────┘
                        │          │          │          │          │
              ┌─────────┤          │          │          │          ├─────────┐
              ▼         ▼          ▼          ▼          ▼          ▼         ▼
        ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
        │ Auth   │ │Catalog │ │Routines│ │Tracking│ │Dashboard│ │ Notif. │ │Storage │
        │ :8001  │ │ :8002  │ │ :8003  │ │ :8004  │ │ :8005  │ │ :8006  │ │ :8002  │
        └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────────┘
            │          │          │          │          │          │
            └──────────┼──────────┼──────────┼──────────┼──────────┘
                       │          │          │          │
              ┌────────▼──────────▼──────────▼──────────▼──────────┐
              │               PostgreSQL (:5432)                   │
              │  users, tracking, routines, exercises,             │
              │  projections, habits, event_queue,                 │
              │  push_subscriptions                                │
              └────────┬──────────┬──────────┬─────────────────────┘
                       │          │          │
                       ▼          ▼          ▼
                 ┌────────┐ ┌────────┐ ┌────────────┐
                 │DuckDB  │ │ Ollama │ │  Workers   │
                 │analytics│ │:11434  │ │replicator  │
                 └────────┘ └────────┘ │preventive  │
                                       │weekly_an.  │
                                       │daily_inact.│
                                       └────────────┘
```

### 4.2 Flujo de Autenticación (JWT + bcrypt)

```
┌──────────┐     ┌──────────────────┐     ┌──────────────┐     ┌────────────┐
│ Cliente  │     │  Auth Service    │     │  passlib     │     │ PostgreSQL │
│          │     │    (:8001)       │     │  (bcrypt)    │     │            │
└────┬─────┘     └────────┬─────────┘     └──────┬───────┘     └─────┬──────┘
     │                    │                      │                   │
     │ POST /auth/register│                      │                   │
     │ {email,password,   │                      │                   │
     │  role,profile}     │                      │                   │
     │───────────────────▶│                      │                   │
     │                    │  bcrypt.hash(pw)     │                   │
     │                    │─────────────────────▶│                   │
     │                    │◀─────────────────────│                   │
     │                    │  "$2b$12$..."        │                   │
     │                    │                      │                   │
     │                    │  INSERT INTO users   │                   │
     │                    │  (email,role,profile,│                   │
     │                    │   password)          │                   │
     │                    │──────────────────────────────────────────▶│
     │  {id, email, role} │                      │                   │
     │◀───────────────────│                      │                   │
     │                    │                      │                   │
     │ POST /auth/login   │                      │                   │
     │ {email,password}   │                      │                   │
     │───────────────────▶│                      │                   │
     │                    │  SELECT * FROM users │                   │
     │                    │  WHERE email=...     │                   │
     │                    │──────────────────────────────────────────▶│
     │                    │◀─────────────────────────────────────────│
     │                    │  {id, password_hash, ...}                │
     │                    │                      │                   │
     │                    │  bcrypt.verify(pw,   │                   │
     │                    │    password_hash)    │                   │
     │                    │─────────────────────▶│                   │
     │                    │◀─────────────────────│                   │
     │                    │  True                │                   │
     │                    │                      │                   │
     │                    │  create_token(id)    │                   │
     │                    │  jwt.encode(payload, │                   │
     │                    │    SECRET, HS256)    │                   │
     │                    │                      │                   │
     │ {access_token,     │                      │                   │
     │  token_type:bearer}│                      │                   │
     │◀───────────────────│                      │                   │
     │                    │                      │                   │
     │ GET /auth/me       │                      │                   │
     │ Authorization:     │                      │                   │
     │ Bearer <token>     │                      │                   │
     │───────────────────▶│                      │                   │
     │                    │  jwt.decode(token)   │                   │
     │                    │  → {sub: user_id}    │                   │
     │                    │                      │                   │
     │                    │  SELECT * FROM users │                   │
     │                    │  WHERE id=sub        │                   │
     │                    │──────────────────────────────────────────▶│
     │                    │◀─────────────────────────────────────────│
     │ {id,email,role,    │                      │                   │
     │  profile,          │                      │                   │
     │  linked_senior_id} │                      │                   │
     │◀───────────────────│                      │                   │
```

### 4.3 Comunicación entre Microservicios

| Origen | Destino | Método | Propósito |
|--------|---------|--------|-----------|
| Gateway (:8000) | Auth (:8001) | Proxy | Ruteo de `/auth/*` |
| Gateway (:8000) | Catalog (:8002) | Proxy | Ruteo de `/catalog/*` y `/storage/*` |
| Gateway (:8000) | Routines (:8003) | Proxy | Ruteo de `/routines/*` |
| Gateway (:8000) | Tracking (:8004) | Proxy | Ruteo de `/tracking/*` |
| Gateway (:8000) | Dashboard (:8005) | Proxy | Ruteo de `/dashboard/*` |
| Gateway (:8000) | Notification (:8006) | Proxy | Ruteo de `/notify/*` |
| Routines (:8003) | Ollama (:11434) | HTTP POST | Generación de rutinas |
| Preventive Worker | Notification (:8006) | HTTP POST | Alerta de fatiga alta |
| Weekly Analysis | Ollama (:11434) | HTTP POST | Generación de insights |
| Tracking (:8004) | event_queue (PG) | INSERT | Publicación de eventos |
| Routines (:8003) | event_queue (PG) | INSERT | Publicación de eventos |
| Replicator | event_queue (PG) | SELECT/UPDATE | Consumo de eventos |
| Preventive Worker | event_queue (PG) | SELECT/UPDATE | Consumo de eventos |
| Replicator | DuckDB | INSERT | Replicación analítica |
| Weekly Analysis | DuckDB | SELECT | Consulta analítica |

### 4.4 Eventos Asíncronos (tabla `event_queue`)

```
┌────────────────────────────────────────────────────────────────────┐
│                      event_queue (PostgreSQL)                      │
│  id BIGSERIAL | stream_name TEXT | payload JSONB | processed BOOL  │
└────────────────────────────────────────────────────────────────────┘

Productores:
  tracking-service ───▶ "ejercicio-completado" ──▶ replicator (DuckDB)
  tracking-service ───▶ "fatiga-alta" ───────────▶ preventive_worker
  routines-ai-service ▶ "rutina-generada" ──────── (sin consumidor)
  daily_inactivity.py ▶ "inactividad-detectada" ── (sin consumidor)
  weekly_analysis.py ─▶ "recomendacion-ajuste" ── (sin consumidor)
```

### 4.5 Tabla de Referencia Cruzada de Archivos

| Archivo | Importa de | Es importado por |
|---------|-----------|-----------------|
| `seniorvital_shared/db.py` | asyncpg, os | Todos los servicios, tests |
| `seniorvital_shared/models.py` | pydantic | auth-profile-service, tests |
| `seniorvital_shared/events.py` | json, .db | routines-ai-service |
| `seniorvital_shared/__init__.py` | .db, .models, .events | Todos |
| `auth-profile-service/main.py` | seniorvital_shared, passlib, jose | tests/conftest (load_service_app) |
| `catalog-service/main.py` | seniorvital_shared, aiofiles | tests/conftest |
| `routines-ai-service/main.py` | seniorvital_shared, httpx | tests/conftest |
| `tracking-service/main.py` | seniorvital_shared | tests/conftest |
| `dashboard-service/main.py` | seniorvital_shared | tests/conftest |
| `notification-service/main.py` | seniorvital_shared, pywebpush | tests/conftest |
| `gateway/main.py` | httpx, fastapi.middleware.cors | — |
| `tests/conftest.py` | seniorvital_shared, importlib | tests/test_*.py |

### 4.6 Esquema de Base de Datos (PostgreSQL + JSONB)

```
┌─────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│     users       │       │    tracking      │       │    routines      │
├─────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id UUID (PK)    │◄──────┤ user_id (FK)     │       │ user_id (FK)     │◄──────┐
│ email TEXT UNQ  │       │ exercise_id TEXT │       │ date DATE        │       │
│ role TEXT       │       │ sets INT         │       │ exercises JSONB  │       │
│ profile JSONB   │       │ reps INT         │       │ warmup JSONB     │       │
│ password TEXT   │       │ rpe INT (1-10)   │       │ active BOOL      │       │
│ linked_senior_id│       │ felt_difficulty  │       └──────────────────┘       │
│ created_at      │       │ completed_at     │                                  │
└─────────────────┘       └──────────────────┘       ┌──────────────────┐       │
        │                                             │  projections    │       │
        │                                             ├──────────────────┤       │
        │◄────────────────────────────────────────────┤ user_id (FK)     │◄──────┘
        │                    (linked_senior_id)       │ week_start DATE  │
        │                                             │ insight_text TEXT│
        │                                             │ estimated_level  │
        │                                             └──────────────────┘
        │
        │              ┌──────────────────┐       ┌──────────────────┐
        │              │   exercises      │       │  event_queue     │
        │              ├──────────────────┤       ├──────────────────┤
        │              │ id UUID (PK)     │       │ id BIGSERIAL(PK) │
        │              │ name TEXT        │       │ stream_name TEXT │
        │              │ level INT (1-4)  │       │ payload JSONB    │
        │              │ contraindications│       │ created_at       │
        │              │ video_url TEXT   │       │ processed BOOL   │
        │              └──────────────────┘       │ processed_at     │
        │                                          └──────────────────┘
        │              ┌──────────────────┐
        │              │push_subscriptions│
        │              ├──────────────────┤
        │              │ user_id TEXT(PK) │
        │              │ endpoint TEXT    │
        │              │ p256dh TEXT      │
        │              │ auth TEXT        │
        │              └──────────────────┘
        │
        │              ┌──────────────────┐
        │              │     habits       │
        │              ├──────────────────┤
        │              │ user_id (FK)     │
        │              │ date DATE        │
        │              │ water_glasses INT│
        │              │ sleep_hours FLOAT│
        │              └──────────────────┘
```

### 4.7 Interacción con Ollama

```
┌──────────────────────┐       ┌──────────────────┐       ┌──────────────┐
│ routines-ai-service  │──────▶│   Ollama Server  │◀──────│weekly_analysis│
│ (:8003)              │ HTTP  │   (:11434)       │ HTTP  │   (.py)      │
│                      │ POST  │                  │ POST  │              │
│ POST /routines/      │──────▶│ POST /api/       │◀──────│              │
│ generate             │       │ generate         │       │              │
│                      │       │                  │       │              │
│ Prompt construido    │       │ Modelo:          │       │ Prompt de    │
│ con perfil de usuario│       │ phi3:mini        │       │ análisis     │
│ + ejercicios seguros │       │                  │       │ semanal      │
│                      │       │ Respuesta:       │       │              │
│ Fallback:            │       │ JSON con rutina  │       │ Fallback:    │
│ DEFAULT_ROUTINE      │       │ o insight        │       │ insight por  │
│ si Ollama no responde│       │                  │       │ defecto      │
└──────────────────────┘       └──────────────────┘       └──────────────┘
```

### 4.8 Pipeline de Pruebas

```
tests/conftest.py
│
├── load_service_app("auth-profile-service")  →  test_auth.py (5 tests)
├── load_service_app("catalog-service")       →  test_catalog.py (6 tests)
├── load_service_app("dashboard-service")     →  test_dashboard.py (3 tests)
├── load_service_app("notification-service")  →  test_notification.py (3 tests)
├── load_service_app("routines-ai-service")   →  test_routines.py (3 tests)
├── load_service_app("tracking-service")      →  test_tracking.py (3 tests)
│
├── auto_init_pool (autouse)
│   └── init_pool(owner="test") → get_pool() para BD real
│
├── cleanup (autouse)
│   └── DELETE FROM todas las tablas
│
└── test_persistence.py (4 tests)
    └── usa seniorvital_shared.HealthProfile + get_pool() directamente
```

---

## 5. Resumen de Puertos y Servicios

| Puerto | Servicio | Tecnología | Dependencia Externa |
|--------|----------|-----------|-------------------|
| 8000 | API Gateway | FastAPI + httpx | — |
| 8001 | Auth Profile | FastAPI + bcrypt + JWT | PostgreSQL |
| 8002 | Catalog | FastAPI + aiofiles | PostgreSQL, filesystem |
| 8003 | Routines AI | FastAPI + httpx | PostgreSQL, Ollama |
| 8004 | Tracking | FastAPI + asyncpg | PostgreSQL |
| 8005 | Dashboard | FastAPI + asyncpg | PostgreSQL, DuckDB |
| 8006 | Notification | FastAPI + pywebpush | PostgreSQL |
| 5432 | PostgreSQL | asyncpg | — |
| 11434 | Ollama | httpx | Modelo phi3:mini |

---

## 6. Variables de Entorno (`.env`)

| Variable | Default | Usada por |
|----------|---------|-----------|
| `DATABASE_URL` | `postgresql://postgres:9739185@localhost:5432/seniorvital` | Todos los servicios y scripts |
| `OLLAMA_URL` | `http://localhost:11434` | routines-ai-service, weekly_analysis |
| `JWT_SECRET` | `super-secret-key-change-in-production` | auth-profile-service |
| `VAPID_PUBLIC_KEY` | `""` | notification-service |
| `VAPID_PRIVATE_KEY` | `""` | notification-service |
| `VAPID_CLAIM_EMAIL` | `admin@seniorvital.com` | notification-service |
