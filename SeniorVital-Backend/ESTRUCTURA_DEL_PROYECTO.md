# Estructura del Proyecto SeniorVital

> Sistema de microservicios backend para gestión de bienestar de adultos mayores.
> FastAPI + PostgreSQL + DuckDB + Ollama (phi3:mini).

---

## Índice de Carpetas

1. [Raíz del proyecto](#1-raíz-del-proyecto)
2. [`auth-profile-service/`](#2-auth-profile-service-port-8001)
3. [`catalog-service/`](#3-catalog-service-port-8002)
4. [`routines-ai-service/`](#4-routines-ai-service-port-8003)
5. [`tracking-service/`](#5-tracking-service-port-8004)
6. [`dashboard-service/`](#6-dashboard-service-port-8005)
7. [`notification-service/`](#7-notification-service-port-8006)
8. [`gateway/`](#8-gateway-port-8000)
9. [`seniorvital_shared/`](#9-seniorvital_shared)
10. [`scripts/`](#10-scripts)
11. [`tests/`](#11-tests)
12. [`storage/`](#12-storage)
13. [`logs/`](#13-logs)

---

## 1. Raíz del proyecto

**Funcionalidad:** Punto de entrada del proyecto. Contiene la configuración global, documentación de alto nivel, esquema de base de datos, dependencias compartidas y archivos de orquestación.

**Uso y aplicabilidad:** Todo el sistema se orquesta desde aquí. Los scripts de inicio/detención usan esta carpeta como directorio base. Cada microservicio la referencia mediante `sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))`.

### Archivos

#### `.env`
- **Funcionalidad:** Variables de entorno en tiempo de ejecución (credenciales PostgreSQL, JWT secret, claves VAPID). Cargado por `python-dotenv` en `tests/conftest.py` y cada microservicio.
- **Conexiones:** `DATABASE_URL` usada por todos los servicios y workers; `JWT_SECRET` usado por `auth-profile-service`; `VAPID_*` usado por `notification-service`.

#### `.env.example`
- **Funcionalidad:** Plantilla de `.env` con valores de ejemplo para facilitar la configuración inicial.
- **Conexiones:** Mismas variables que `.env`.

#### `AGENTS.md`
- **Funcionalidad:** Instrucciones para OpenCode (agente de IA), describe estructura del proyecto, comandos, dependencias y arquitectura.
- **Conexiones:** Guía al agente sobre cómo navegar y modificar el proyecto.

#### `ARQUITECTURA.md`
- **Funcionalidad:** Mapa detallado de arquitectura con descripción de cada archivo y sus relaciones.
- **Conexiones:** Documentación de referencia para desarrolladores.

#### `GUIA_DESARROLLO.md`
- **Funcionalidad:** Guía completa de desarrollo con 12 secciones (instalación, arquitectura, testing, despliegue).
- **Conexiones:** Complemento de `README.md` con información más detallada.

#### `README.md`
- **Funcionalidad:** Documentación principal del proyecto en inglés. Describe propósito, stack, instalación y uso.
- **Conexiones:** Puerta de entrada para nuevos desarrolladores.

#### `REQUISITOS_FUNCIONALES.md`
- **Funcionalidad:** 91 requisitos funcionales y 14 criterios de aceptación (AC) mapeados contra los tests.
- **Conexiones:** Cada `test_*.py` cubre uno o más AC documentados aquí.

#### `SDD.md`
- **Funcionalidad:** System Design Document (858 líneas) — fuente de verdad de la especificación técnica. No modificable.
- **Conexiones:** Todos los servicios, workers y pruebas se implementan según esta especificación.

#### `init_db.sql`
- **Funcionalidad:** Script SQL completo con el esquema de PostgreSQL (8 tablas: `users`, `tracking`, `habits`, `routines`, `projections`, `exercises`, `event_queue`, `push_subscriptions`). Ya ejecutado.
- **Conexiones:** La estructura de tablas que todos los servicios consultan mediante asyncpg.

#### `pytest.ini`
- **Funcionalidad:** Configuración de pytest con `asyncio_mode=auto`.
- **Conexiones:** Afecta a todos los archivos en `tests/`.

#### `requirements.txt`
- **Funcionalidad:** Dependencias Python globales del proyecto (fastapi, uvicorn, asyncpg, passlib, python-jose, pydantic, httpx, duckdb, pywebpush, pytest, bcrypt).
- **Conexiones:** Instalado por `pip install -r requirements.txt` en cada entorno.

#### `seniorvital_analytics.duckdb`
- **Funcionalidad:** Base de datos DuckDB embebida para análisis. Contiene tablas `raw_events` y `weekly_progress`.
- **Conexiones:** Escrita por `scripts/replicator.py`; leída por `scripts/weekly_analysis.py` y `dashboard-service`.

#### `seniorvital-frontend.zip`
- **Funcionalidad:** Archivo comprimido del frontend (no forma parte del backend).
- **Conexiones:** No tiene dependencias con el backend más allá de las APIs REST.

---

## 2. `auth-profile-service/` (port 8001)

**Funcionalidad:** Autenticación de usuarios y gestión de perfiles. Registro, inicio de sesión (JWT + bcrypt), consulta y actualización de perfil de salud, y vinculación entre seniors y cuidadores.

**Uso y aplicabilidad:** Microservicio independiente con su propio pool de conexiones. Es el punto de entrada para todos los usuarios del sistema. Sin este servicio, ningún otro puede operar porque todos requieren un `user_id` válido para las claves foráneas.

### Archivos

#### `main.py`
- **Funcionalidad:** Define los endpoints REST del servicio:
  - `POST /auth/register` — Registro con email, password, rol (senior/caregiver), y perfil de salud opcional. Hashea password con bcrypt. Valida: rol permitido, caregiver sin linked_senior_id preexistente, máximo 3 cuidadores por senior, caregiver con un solo senior.
  - `POST /auth/login` — Autenticación por email+password. Retorna JWT (HS256, expira 7 días) e información del usuario.
  - `GET /auth/me` — Obtiene perfil del usuario autenticado (requiere token Bearer).
  - `PUT /auth/profile` — Actualiza perfil de salud (HealthProfile validado).
  - `POST /auth/link-caregiver/{senior_id}` — Vincula un caregiver a un senior (requiere token de caregiver, verifica límites).
- **Conexiones:** `seniorvital_shared/db.py` (pool), `seniorvital_shared/models.py` (HealthProfile), `passlib.hash.bcrypt`, `jose.jwt`. Tabla `users` en PostgreSQL.

#### `requirements.txt`
- **Funcionalidad:** Dependencias específicas del servicio (fastapi, uvicorn, asyncpg, passlib, python-jose, python-dotenv).
- **Conexiones:** Subconjunto de `requirements.txt` raíz.

---

## 3. `catalog-service/` (port 8002)

**Funcionalidad:** Catálogo de ejercicios con operaciones CRUD y almacenamiento/servicio de videos.

**Uso y aplicabilidad:** Microservicio independiente. Proporciona los ejercicios que luego usa `routines-ai-service` para generar rutinas. También sirve archivos de video almacenados localmente.

### Archivos

#### `main.py`
- **Funcionalidad:** Endpoints REST:
  - `GET /catalog/exercises` — Lista ejercicios con filtros opcionales (level 1-4, nombre).
  - `POST /catalog/exercises` — Crea ejercicio (name, level, contraindications, video_url).
  - `GET /catalog/exercises/{id}` — Obtiene un ejercicio por ID.
  - `PUT /catalog/exercises/{id}` — Actualiza campos de un ejercicio.
  - `DELETE /catalog/exercises/{id}` — Elimina un ejercicio.
  - `POST /catalog/exercises/{id}/video` — Sube archivo de video (máx 50 MB, validación de extensión).
  - `GET /catalog/video/{filename}` — Sirve video almacenado como FileResponse.
- **Conexiones:** `seniorvital_shared/db.py`, `aiofiles` para lectura de archivos. Tabla `exercises`. Carpeta `storage/videos/` para almacenamiento físico.

#### `requirements.txt`
- **Funcionalidad:** fastapi, uvicorn, asyncpg, aiofiles, python-multipart, python-dotenv.
- **Conexiones:** `python-multipart` necesario para recibir archivos via upload.

---

## 4. `routines-ai-service/` (port 8003)

**Funcionalidad:** Generación de rutinas de ejercicio personalizadas mediante IA (Ollama con phi3:mini). Usa el perfil de salud del usuario y los ejercicios del catálogo respetando restricciones médicas.

**Uso y aplicabilidad:** Microservicio independiente con conexión a Ollama. Es el componente "inteligente" del sistema. Si Ollama falla, usa una rutina por defecto como fallback.

### Archivos

#### `main.py`
- **Funcionalidad:** Endpoints REST:
  - `POST /routines/generate` — Genera rutina para hoy. Busca usuario en DB, obtiene su perfil, consulta ejercicios seguros (sin contraindicaciones), construye prompt para Ollama, parsea respuesta JSON, persiste en tabla `routines`. Si ya existe rutina activa para hoy y `force=false`, la retorna. Publica evento `rutina-generada`.
  - `GET /routines/today` — Obtiene la rutina activa del día de un usuario.
  - `call_ollama(prompt)` — Función interna que llama a `http://localhost:11434/api/generate` con el modelo `phi3:mini` y timeout de 180s.
  - `build_prompt(profile, safe_exercises)` — Construye el prompt estructurado para el modelo.
  - `DEFAULT_ROUTINE` — Rutina de fallback (caminata ligera, estiramiento, respiración).
- **Conexiones:** `seniorvital_shared/db.py`, `seniorvital_shared/events.py` (publish_event), `httpx` (cliente HTTP a Ollama). Tablas: `users`, `exercises`, `routines`, `event_queue`.

#### `requirements.txt`
- **Funcionalidad:** fastapi, uvicorn, asyncpg, httpx, python-dotenv.
- **Conexiones:** `httpx` necesario para la comunicación asíncrona con Ollama.

---

## 5. `tracking-service/` (port 8004)

**Funcionalidad:** Registro de ejercicios completados por los usuarios con detección de fatiga alta y publicación de eventos asíncronos.

**Uso y aplicabilidad:** Microservicio independiente. Es el principal generador de datos para el dashboard y los workers. Cada vez que un usuario completa un ejercicio, este servicio registra el tracking y publica eventos en `event_queue`.

### Archivos

#### `main.py`
- **Funcionalidad:** Endpoints REST:
  - `POST /tracking/record` — Registra un ejercicio (user_id, exercise_id, sets, reps, rpe, felt_difficulty, completed_at). Dentro de una transacción: inserta en `tracking`, publica evento `ejercicio-completado`, y si rpe >= 8 publica evento `fatiga-alta`.
  - `POST /tracking/batch` — Registra múltiples ejercicios en una sola transacción atómica. Retorna IDs y conteo.
  - Modelos Pydantic: `TrackEntry` (user_id, exercise_id, sets, reps, rpe opcional, felt_difficulty opcional, completed_at opcional), `BatchTrackRequest` (entries: list[TrackEntry]).
- **Conexiones:** `seniorvital_shared/db.py`, `seniorvital_shared/events.py`. Tablas: `tracking` (con FK a users y exercises), `event_queue`. El worker `preventive_worker.py` consume los eventos `fatiga-alta` que publica.

#### `requirements.txt`
- **Funcionalidad:** fastapi, uvicorn, asyncpg, python-dotenv.
- **Conexiones:** No requiere dependencias externas adicionales.

---

## 6. `dashboard-service/` (port 8005)

**Funcionalidad:** Consultas agregadas de progreso semanal, proyecciones generadas por IA e insights históricos.

**Uso y aplicabilidad:** Microservicio independiente de solo lectura (GET). Consulta datos agregados de `tracking` y `projections`. Es el servicio que alimenta las vistas del frontend.

### Archivos

#### `main.py`
- **Funcionalidad:** Endpoints REST:
  - `GET /dashboard/progress/{user_id}` — Resumen semanal: calendario de repeticiones, tendencia de RPE, racha de días consecutivos, total de sesiones en la semana. Retorna 404 si el usuario no existe.
  - `GET /dashboard/projection/{user_id}` — Última proyección generada por el agente semanal (de tabla `projections`). Retorna `{"projection": null}` si no existe.
  - `GET /dashboard/insights/{user_id}` — Historial de hasta 10 insights ordenados por semana descendente.
- **Conexiones:** `seniorvital_shared/db.py`. Tablas: `users`, `tracking`, `projections`. Los datos de `projections` son escritos por `scripts/weekly_analysis.py`.

#### `requirements.txt`
- **Funcionalidad:** fastapi, uvicorn, asyncpg, python-dotenv.
- **Conexiones:** Mismas dependencias que tracking-service.

---

## 7. `notification-service/` (port 8006)

**Funcionalidad:** Notificaciones push mediante Web Push API con claves VAPID. Gestión de suscripciones y envío asíncrono.

**Uso y aplicabilidad:** Microservicio independiente. Maneja suscripciones de usuarios y envía notificaciones en segundo plano. Otros servicios (como `preventive_worker`) le envían peticiones HTTP para notificar a usuarios.

### Archivos

#### `main.py`
- **Funcionalidad:** Endpoints REST:
  - `POST /notify/subscribe` — Guarda o sobrescribe suscripción push de un usuario (user_id, subscription con endpoint + keys.p256dh + keys.auth).
  - `POST /notify/send` — Encola envío de notificación como tarea de fondo (BackgroundTasks). Llama a `send_push_notification()`.
  - `send_push_notification(user_id, title, body)` — Función interna que consulta suscripción, construye `sub_info`, llama a `pywebpush.webpush()`. Si el endpoint responde 410 Gone, elimina la suscripción.
- **Conexiones:** `seniorvital_shared/db.py`, `pywebpush`. Tabla `push_subscriptions`. Variables de entorno `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIM_EMAIL`. Es llamado por `preventive_worker.py` via HTTP.

#### `requirements.txt`
- **Funcionalidad:** fastapi, uvicorn, asyncpg, pywebpush, python-dotenv.
- **Conexiones:** `pywebpush` es la única dependencia distintiva.

---

## 8. `gateway/` (port 8000)

**Funcionalidad:** API Gateway / proxy inverso. Redirige peticiones al microservicio correspondiente según el prefijo de la ruta.

**Uso y aplicabilidad:** Punto de entrada único para clientes externos. Enruta a los microservicios internos. Sin él, los clientes necesitarían conocer la dirección de cada servicio individual.

### Archivos

#### `main.py`
- **Funcionalidad:** Proxy inverso con una sola ruta comodín:
  - `/{path:path}` (GET, POST, PUT, DELETE, PATCH) — Captura toda petición, busca el prefijo en `ROUTES`, reenvía la petición completa (método, body, headers, query params) al microservicio destino, y retorna la respuesta.
  - `ROUTES` — Mapa de prefijos a URLs destino: `/auth/` -> `:8001`, `/catalog/` -> `:8002`, `/routines/` -> `:8003`, `/tracking/` -> `:8004`, `/dashboard/` -> `:8005`, `/notify/` -> `:8006`, `/storage/` -> `:8002`.
  - Middleware CORS permite origen `http://localhost:3000`.
  - Retorna 502 "No route found" si el prefijo no coincide, o "Service unavailable" si el destino no responde.
- **Conexiones:** `httpx` como cliente HTTP asíncrono. Se comunica con todos los 6 microservicios. No usa `seniorvital_shared` ni base de datos.

#### `requirements.txt`
- **Funcionalidad:** fastapi, uvicorn, httpx, python-dotenv.
- **Conexiones:** `httpx` es la única dependencia significativa.

---

## 9. `seniorvital_shared/`

**Funcionalidad:** Biblioteca compartida por todos los microservicios. Gestiona el pool de conexiones a PostgreSQL y define modelos de datos comunes.

**Uso y aplicabilidad:** Paquete Python importado por cada servicio mediante `sys.path.insert(0, ...)`. NO es un microservicio — es código reutilizable empaquetado como módulo.

### Archivos

#### `__init__.py`
- **Funcionalidad:** Exporta símbolos públicos: `get_pool`, `init_pool`, `close_pool`, `HealthProfile`, `publish_event`.
- **Conexiones:** Todos los servicios importan desde aquí: `from seniorvital_shared import get_pool, HealthProfile, ...`.

#### `db.py`
- **Funcionalidad:** Singleton del pool de conexiones asyncpg con sistema de "owners". Funciones:
  - `init_pool(owner, min_size, max_size)` — Crea pool si no existe; si existe, registra el owner.
  - `get_pool()` — Retorna el pool (lanza error si no hay pool inicializado).
  - `close_pool(owner)` — Desregistra owner; solo cierra el pool cuando no quedan owners.
- **Conexiones:** Usado por todos los servicios y scripts. El sistema de owners permite que múltiples servicios compartan el pool sin cierres prematuros (crítico para tests).

#### `models.py`
- **Funcionalidad:** Define `HealthProfile(BaseModel)` con validación Pydantic v2 (`field_validator`):
  - Campos: age (60-120), weight_kg (30-200), height_cm (100-250), fitness_level (principiante|intermedio|avanzado), goals (min 1), medical_restrictions (lista con valores permitidos: artrosis_rodilla, osteoporosis, hipertensión, dolor_articular, prótesis), equipment, preferred_schedule.
- **Conexiones:** Usado por `auth-profile-service` para validar perfiles al registrar/actualizar. El perfil se almacena como TEXT/JSON en tabla `users`.

#### `events.py`
- **Funcionalidad:** Función `publish_event(stream_name, payload)` que inserta una fila en `event_queue` con el payload como JSON string.
- **Conexiones:** Usado por `routines-ai-service` y `tracking-service` para publicar eventos. Los workers (`replicator`, `preventive_worker`, etc.) consumen de `event_queue`.

---

## 10. `scripts/`

**Funcionalidad:** Automatización y procesos background. Incluye workers asíncronos, scripts de inicio/parada, migraciones y tests de integración.

**Uso y aplicabilidad:** Scripts ejecutables independientemente. Los workers son procesos de larga duración con polling loops. Los scripts de inicio/parada orquestan todos los servicios.

### Archivos

#### `replicator.py`
- **Funcionalidad:** Worker que cada 1s consulta eventos `ejercicio-completado` no procesados en `event_queue`, los replica en DuckDB (tabla `raw_events`) y actualiza `weekly_progress` (DELETE + INSERT porque DuckDB no tiene PK/UNIQUE en esa tabla). Marca eventos como `processed = TRUE`.
- **Conexiones:** `asyncpg` a PostgreSQL, `duckdb` a `seniorvital_analytics.duckdb`. Lee de `event_queue`, escribe en `raw_events` y `weekly_progress`.

#### `preventive_worker.py`
- **Funcionalidad:** Worker que cada 2s consulta eventos `fatiga-alta` no procesados, loggea advertencia (user, rpe_value), envía notificación push vía `http://localhost:8006/notify/send`, y marca como procesado.
- **Conexiones:** `asyncpg` a PostgreSQL, `httpx` a `notification-service`. Lee de `event_queue`, escribe en `event_queue` (processed).

#### `weekly_analysis.py`
- **Funcionalidad:** Análisis semanal: lee `weekly_progress` de DuckDB, para cada usuario llama a Ollama para generar insight (texto + nivel estimado), guarda en `projections` (PostgreSQL), publica evento `recomendacion-ajuste`. Filtra user_ids no-UUID. Timeout Ollama 180s.
- **Conexiones:** `asyncpg`, `duckdb`, `httpx` a Ollama. Lee de DuckDB, escribe en `projections` y `event_queue`. Los insights son servidos por `dashboard-service`.

#### `daily_inactivity.py`
- **Funcionalidad:** Detecta seniors sin tracking en los últimos 4+ días. Para cada uno, publica evento `inactividad-detectada` con `days_inactive`.
- **Conexiones:** `asyncpg`. Lee de `users` y `tracking`, escribe en `event_queue`.

#### `smoke_test.py`
- **Funcionalidad:** Suite de tests de integración (16 tests) contra servicios reales en ejecución. Prueba todos los endpoints de todos los servicios secuencialmente.
- **Conexiones:** `httpx` a todos los servicios en localhost:8000-8006.

#### `migrations.sql`
- **Funcionalidad:** Migraciones DDL: `ALTER TABLE users ADD COLUMN password`, `CREATE TABLE push_subscriptions`.
- **Conexiones:** Ejecutado contra PostgreSQL. Afecta a `auth-profile-service` (password) y `notification-service` (push_subscriptions).

#### `start_all.ps1` / `start_all.sh`
- **Funcionalidad:** Inicia los 7 servicios como procesos background (PowerShell Jobs o `&`). Espera 5s entre cada uno. Guarda PIDs en `logs/*.pid`.
- **Conexiones:** Ejecuta `uvicorn main:app --host 0.0.0.0 --port <port>` en cada directorio de servicio.

#### `stop_all.ps1` / `stop_all.sh`
- **Funcionalidad:** Detiene los servicios leyendo PIDs de `logs/*.pid` y matando procesos.
- **Conexiones:** Lee archivos escritos por `start_all.ps1/sh`.

---

## 11. `tests/`

**Funcionalidad:** Suite completa de pruebas con pytest (27 tests). Cubre todos los criterios de aceptación (AC-*) definidos en SDD.md.

**Uso y aplicabilidad:** Ejecutable con `pytest tests/ -v`. Usa ASGITransport de httpx para probar servicios sin servidor real. Cada test limpia datos después de ejecutarse.

### Archivos

#### `__init__.py`
- **Funcionalidad:** Archivo vacío que marca `tests/` como paquete Python.
- **Conexiones:** Permite importaciones relativas entre test files.

#### `conftest.py`
- **Funcionalidad:** Fixtures compartidos:
  - `load_service_app(service_name)` — Carga dinámicamente la app FastAPI de un servicio usando `importlib` (convierte guiones a guiones bajos en el nombre del módulo).
  - `auto_init_pool` — Fixture autouse que inicializa pool con owner="test" antes de cada test y lo cierra después.
  - `cleanup` — Fixture autouse que después de cada test elimina datos de todas las tablas (event_queue, tracking, routines, projections, push_subscriptions, exercises, habits, users).
- **Conexiones:** `seniorvital_shared`, `importlib`, `dotenv`. Carga las apps de los servicios dinámicamente.

#### `test_auth.py`
- **Funcionalidad:** 5 tests:
  - `test_ac_auth_01_password_hashed` — Verifica que password se almacena hasheado con bcrypt.
  - `test_ac_auth_02_invalid_role` — Rechaza roles no válidos.
  - `test_ac_auth_03_caregiver_no_linked` — Caregiver se registra sin linked_senior_id.
  - `test_ac_auth_04_max_3_caregivers` — Senior no puede tener más de 3 cuidadores.
  - `test_ac_auth_05_caregiver_one_linked` — Caregiver solo puede tener un senior vinculado.
- **Conexiones:** Usa `conftest.load_service_app("auth-profile-service")`. Tabla `users`.

#### `test_catalog.py`
- **Funcionalidad:** 6 tests: CRUD completo de ejercicios + subida y descarga de video.
- **Conexiones:** Usa `load_service_app("catalog-service")`. Tabla `exercises`. Carpeta `storage/videos/`.

#### `test_dashboard.py`
- **Funcionalidad:** 3 tests: progress (usuario no existe retorna 404), projection (retorna null si no existe), insights (lista vacía si no hay datos).
- **Conexiones:** Usa `load_service_app("dashboard-service")`. Tablas `users`, `tracking`, `projections`.

#### `test_notification.py`
- **Funcionalidad:** 3 tests: suscripción, sobrescritura de suscripción (AC-NOT-01), envío de notificación en background (AC-NOT-02).
- **Conexiones:** Usa `load_service_app("notification-service")`. Tabla `push_subscriptions`.

#### `test_persistence.py`
- **Funcionalidad:** 4 tests: HealthProfile válido, HealthProfile con restricción inválida, caregiver vinculado a senior, inserción en event_queue.
- **Conexiones:** Usa `seniorvital_shared` directamente. Tablas `users`, `event_queue`.

#### `test_routines.py`
- **Funcionalidad:** 3 tests: generar rutina con usuario inexistente (404), consultar rutina de hoy sin rutina (404), generar rutina dos veces retorna la existente (con Ollama mockeado via `__globals__`).
- **Conexiones:** Usa `load_service_app("routines-ai-service")`. Tablas `users`, `routines`. Mockea `call_ollama` en `__globals__` del endpoint.

#### `test_tracking.py`
- **Funcionalidad:** 3 tests: registro individual (con seed_users que crea usuarios reales), fatiga alta (RPE 9 publica evento), registro por lote con 2 entradas.
- **Conexiones:** Usa `load_service_app("tracking-service")`. Tablas `users`, `tracking`, `event_queue`.

#### Archivos auxiliares (`test_db_conn.py`, `get_pgpass.py`, `get_pg_credential.py`, `get_pg_credential2.py`, `get_windows_credential.py`)
- **Funcionalidad:** Scripts de diagnóstico para obtener credenciales PostgreSQL de diversas fuentes (pgAdmin SQLite, Windows Credential Manager, Win32 API). No son tests formales.
- **Conexiones:** Usados durante la configuración inicial del proyecto para descubrir la contraseña de PostgreSQL.

---

## 12. `storage/`

**Funcionalidad:** Almacenamiento local de archivos multimedia (videos de ejercicios y fotos de progreso).

**Uso y aplicabilidad:** Directorios montados/servidos por `catalog-service` mediante `FileResponse` de Starlette. Los videos se sirven en `GET /catalog/video/{filename}`.

### Archivos

#### `videos/`
- **Funcionalidad:** Contiene 12 archivos `.mp4` de demostración para ejercicios. Creado por `start_all.ps1` si no existe.
- **Conexiones:** Servido por `catalog-service/main.py` línea ~200 (`FileResponse`). Escrito por `POST /catalog/exercises/{id}/video`.

#### `progress-photos/`
- **Funcionalidad:** Carpeta vacía preparada para futuras fotos de progreso de usuarios.
- **Conexiones:** No implementado actualmente.

---

## 13. `logs/`

**Funcionalidad:** Directorio runtime para archivos de log y PID de cada servicio.

**Uso y aplicabilidad:** Creado por `start_all.ps1`. Cada servicio escribe su log en `logs/<nombre>.log` y su PID en `logs/<nombre>.pid`. Usado por `stop_all.ps1` para localizar y matar procesos.

### Archivos (generados en ejecución)

- `auth-profile.log`, `catalog.log`, `routines-ai.log`, `tracking.log`, `dashboard.log`, `notification.log`, `gateway.log`
- `auth-profile.pid`, `catalog.pid`, `routines-ai.pid`, `tracking.pid`, `dashboard.pid`, `notification.pid`, `gateway.pid`
