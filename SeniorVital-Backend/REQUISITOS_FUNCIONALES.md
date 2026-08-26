# Requisitos Funcionales por Microservicio — SeniorVital

Basado en SDD.md (secciones 3–6) y la implementación desarrollada.

---

## 1. API Gateway (`:8000`)

| ID | Requisito | Estado |
|----|-----------|--------|
| RF-GW-001 | Escuchar en `0.0.0.0:8000` | ✅ |
| RF-GW-002 | Redirigir `/auth/*` → `auth-profile-service:8001` | ✅ |
| RF-GW-003 | Redirigir `/catalog/*` → `catalog-service:8002` | ✅ |
| RF-GW-004 | Redirigir `/routines/*` → `routines-ai-service:8003` | ✅ |
| RF-GW-005 | Redirigir `/tracking/*` → `tracking-service:8004` | ✅ |
| RF-GW-006 | Redirigir `/dashboard/*` → `dashboard-service:8005` | ✅ |
| RF-GW-007 | Redirigir `/notify/*` → `notification-service:8006` | ✅ |
| RF-GW-008 | Redirigir `/storage/*` → `catalog-service:8002` | ✅ |
| RF-GW-009 | No modificar cuerpos de peticiones ni respuestas | ✅ |
| RF-GW-010 | Soportar CORS para origen `http://localhost:3000` | ✅ |
| RF-GW-011 | Soportar métodos GET, POST, PUT, DELETE, PATCH en catch-all | ✅ |

---

## 2. Auth-Profile Service (`:8001`)

### 2.1 Registro

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-AUTH-001 | Validar que `role` sea uno de: `senior`, `caregiver`, `admin` | SPEC-AUTH-REG | ✅ |
| RF-AUTH-002 | Rechazar con HTTP 400 si `role` no es válido | AC-AUTH-02 | ✅ |
| RF-AUTH-003 | Validar `profile` contra esquema `HealthProfile` (Pydantic) si se envía | SPEC-AUTH-REG | ✅ |
| RF-AUTH-004 | Hashear contraseña con bcrypt antes de almacenar | AC-AUTH-01 | ✅ |
| RF-AUTH-005 | Insertar registro en tabla `users` con email, role, profile (JSON), password | SPEC-AUTH-REG | ✅ |
| RF-AUTH-006 | Rechazar con HTTP 400 si el email ya existe | SPEC-AUTH-REG precond | ✅ |
| RF-AUTH-007 | Si `role=caregiver` y no se envía `linked_senior_id`, queda NULL | AC-AUTH-03 | ✅ |
| RF-AUTH-008 | Devolver `{id, email, role}` en respuesta exitosa | SPEC-AUTH-REG | ✅ |

### 2.2 Login

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-AUTH-009 | Verificar contraseña contra hash bcrypt almacenado | — | ✅ |
| RF-AUTH-010 | Devolver JWT (HS256, 7 días de expiración) | SPEC-AUTH-LOGIN | ✅ |
| RF-AUTH-011 | Rechazar con HTTP 401 si credenciales inválidas | — | ✅ |

### 2.3 Perfil (`/auth/me`)

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-AUTH-012 | Requerir token Bearer válido | — | ✅ |
| RF-AUTH-013 | Devolver `{id, email, role, profile, linked_senior_id}` | — | ✅ |
| RF-AUTH-014 | Devolver HTTP 404 si usuario no existe | — | ✅ |

### 2.4 Actualizar Perfil

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-AUTH-015 | Solo permitir a usuarios con `role=senior` o `role=admin` | — | ✅ |
| RF-AUTH-016 | Rechazar con HTTP 403 si role no autorizado | — | ✅ |
| RF-AUTH-017 | Validar nuevo `profile` contra `HealthProfile` | — | ✅ |
| RF-AUTH-018 | Actualizar columna `profile` en PostgreSQL | — | ✅ |

### 2.5 Vincular Caregiver

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-AUTH-019 | Requerir usuario autenticado con `role=senior` | SPEC-AUTH-LINK | ✅ |
| RF-AUTH-020 | Rechazar con HTTP 403 si el usuario no es senior | — | ✅ |
| RF-AUTH-021 | Buscar caregiver por email con `role=caregiver` | SPEC-AUTH-LINK | ✅ |
| RF-AUTH-022 | Rechazar con HTTP 404 si caregiver no existe | — | ✅ |
| RF-AUTH-023 | Limitar a máximo 3 caregivers vinculados por senior | AC-AUTH-04 | ✅ |
| RF-AUTH-024 | Rechazar con HTTP 400 si ya hay 3 caregivers | — | ✅ |
| RF-AUTH-025 | Rechazar con HTTP 400 si el caregiver ya está vinculado a otro senior | AC-AUTH-05 | ✅ |
| RF-AUTH-026 | Actualizar `linked_senior_id` del caregiver con el ID del senior | SPEC-AUTH-LINK postcond | ✅ |

---

## 3. Catalog Service (`:8002`)

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-CAT-001 | Listar ejercicios con filtros opcionales: `level` (1–4), `name` (ILIKE) | SPEC-CAT-001 | ✅ |
| RF-CAT-002 | Crear nuevo ejercicio con `name`, `level`, `contraindications[]`, `video_url?` | — | ✅ |
| RF-CAT-003 | Devolver HTTP 201 con `{id, name}` al crear | — | ✅ |
| RF-CAT-004 | Obtener detalle de un ejercicio por ID | — | ✅ |
| RF-CAT-005 | Actualizar campos de un ejercicio por ID | — | ✅ |
| RF-CAT-006 | Eliminar un ejercicio por ID | — | ✅ |
| RF-CAT-007 | Devolver HTTP 404 si ejercicio no existe en GET/PUT/DELETE | — | ✅ |
| RF-CAT-008 | Subir archivo de video MP4 (max 50MB) para un ejercicio | SPEC-CAT-002 | ✅ |
| RF-CAT-009 | Guardar video en `storage/videos/<uuid>.mp4` | SPEC-CAT-002 | ✅ |
| RF-CAT-010 | Actualizar `video_url` del ejercicio con la URL resultante | SPEC-CAT-002 | ✅ |
| RF-CAT-011 | Validar tipo MIME `video/*` en subida | — | ✅ |
| RF-CAT-012 | Servir archivos de video estáticos vía GET `/storage/videos/{filename}` | SPEC-CAT-002 | ✅ |

---

## 4. Routines-AI Service (`:8003`)

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-RTN-001 | Obtener perfil del usuario desde `users` | SPEC-RTN-001 | ✅ |
| RF-RTN-002 | Consultar ejercicios del catálogo filtrando por contraindicaciones vs restricciones médicas | SPEC-RTN-001(2) | ✅ |
| RF-RTN-003 | Construir prompt para Ollama con perfil + ejercicios seguros | SPEC-RTN-001(3) | ✅ |
| RF-RTN-004 | Llamar a Ollama (`phi3:mini`) con el prompt | SPEC-RTN-001(4) | ✅ |
| RF-RTN-005 | Parsear respuesta JSON de Ollama | SPEC-RTN-001(5) | ✅ |
| RF-RTN-006 | Usar rutina por defecto si Ollama falla (fallback) | AC-RTN-02 | ✅ |
| RF-RTN-007 | Guardar rutina en tabla `routines` con user_id, date, exercises, warmup | SPEC-RTN-001(6) | ✅ |
| RF-RTN-008 | Publicar evento `rutina-generada` en `event_queue` | SPEC-RTN-001(7) | ✅ |
| RF-RTN-009 | Si `force=false` y ya existe rutina activa para hoy, devolver la existente | — | ✅ |
| RF-RTN-010 | Rechazar con HTTP 404 si user_id no existe | — | ✅ |
| RF-RTN-011 | Respetar restricciones médicas del perfil (no sugerir ejercicios contraindicados) | AC-RTN-03 | ✅ |
| RF-RTN-012 | Obtener rutina del día desde `/routines/today?user_id={id}` | — | ✅ |

---

## 5. Tracking Service (`:8004`)

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-TRK-001 | Insertar registro en tabla `tracking` con user_id, exercise_id, sets, reps, rpe, felt_difficulty, completed_at | SPEC-TRK-001 | ✅ |
| RF-TRK-002 | Insertar evento `ejercicio-completado` en `event_queue` con payload completo | SPEC-TRK-001(2) | ✅ |
| RF-TRK-003 | Si `rpe >= 8`, insertar evento adicional `fatiga-alta` en `event_queue` | SPEC-TRK-001(3) | ✅ |
| RF-TRK-004 | Ejecutar inserción en tracking + eventos en una sola transacción atómica | SPEC-TRK-001 | ✅ |
| RF-TRK-005 | Devolver `{id, detail}` en registro individual | — | ✅ |
| RF-TRK-006 | Soportar registro por lote (`/tracking/batch`) con múltiples entradas | SPEC-TRK-002 | ✅ |
| RF-TRK-007 | Devolver `{ids, count}` en registro por lote | — | ✅ |
| RF-TRK-008 | Validar foreign key `user_id` contra tabla `users` | — | ✅ |

---

## 6. Dashboard Service (`:8005`)

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-DASH-001 | Devolver resumen de progreso semanal: calendario de reps por día, tendencia RPE, racha, total sesiones | SPEC-DASH-001 | ✅ |
| RF-DASH-002 | Devolver última proyección desde tabla `projections` (o null si no existe) | SPEC-DASH-002 | ✅ |
| RF-DASH-003 | Devolver lista de últimos 10 insights desde `projections` | — | ✅ |
| RF-DASH-004 | Respuesta < 1 segundo para usuarios con hasta 3 meses de historial | AC-DASH-01 | ✅ |

---

## 7. Notification Service (`:8006`)

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-NOT-001 | Guardar suscripción Web Push (endpoint, p256dh, auth) por user_id | SPEC-NOT-001 | ✅ |
| RF-NOT-002 | Sobrescribir suscripción existente si el usuario ya tenía una (upsert) | AC-NOT-01 | ✅ |
| RF-NOT-003 | Enviar notificación push usando pywebpush con claves VAPID | SPEC-NOT-002 | ✅ |
| RF-NOT-004 | Ejecutar envío como background task de FastAPI (no bloqueante) | AC-NOT-02 | ✅ |
| RF-NOT-005 | Eliminar suscripción si endpoint devuelve HTTP 410 Gone | SPEC-NOT-002 | ✅ |
| RF-NOT-006 | Almacenar suscripciones en tabla `push_subscriptions` | SPEC-NOT-001 | ✅ |

---

## 8. Persistencia — PostgreSQL

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-PERS-001 | Tabla `users` con campos: id, email, role, profile (JSONB), linked_senior_id, password, created_at | §3.1 | ✅ |
| RF-PERS-002 | Tabla `tracking` con FK a users, completed_at, exercise_id, sets, reps, rpe, felt_difficulty | §3.1 | ✅ |
| RF-PERS-003 | Tabla `habits` con user_id, date, water_glasses, sleep_hours | §3.1 | ✅ |
| RF-PERS-004 | Tabla `routines` con user_id, date, exercises (JSONB), warmup (JSONB), active | §3.1 | ✅ |
| RF-PERS-005 | Tabla `projections` con user_id, week_start, insight_text, estimated_level | §3.1 | ✅ |
| RF-PERS-006 | Tabla `exercises` con name, level (1–4), contraindications (TEXT[]), video_url | §3.1 | ✅ |
| RF-PERS-007 | Tabla `event_queue` con id (BIGSERIAL), stream_name, payload (JSONB), processed, created_at, processed_at | §5 | ✅ |
| RF-PERS-008 | Tabla `push_subscriptions` con user_id (PK), endpoint, p256dh, auth | SPEC-NOT-001 | ✅ |
| RF-PERS-009 | Índices en tracking(user_id, completed_at DESC), exercises(level), users(role), event_queue(stream, processed, created_at) | §3.1 | ✅ |
| RF-PERS-010 | Columna `password` en tabla `users` (agregada vía migration) | — | ✅ |
| RF-PERS-011 | Validar esquema `profile` (JSONB) con `HealthProfile` Pydantic antes de insertar | AC-PERS-02 | ✅ |
| RF-PERS-012 | `linked_senior_id` solo no nulo cuando `role=caregiver` | AC-PERS-03 | ✅ |

---

## 9. Eventos Asíncronos

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-EVT-001 | Publicar evento `ejercicio-completado` desde tracking-service | §5.1 | ✅ |
| RF-EVT-002 | Publicar evento `fatiga-alta` desde tracking-service (si rpe >= 8) | §5.1 | ✅ |
| RF-EVT-003 | Publicar evento `rutina-generada` desde routines-ai-service | §5.1 | ✅ |
| RF-EVT-004 | Publicar evento `inactividad-detectada` desde daily_inactivity.py | §5.1 | ✅ |
| RF-EVT-005 | Publicar evento `recomendacion-ajuste` desde weekly_analysis.py | §5.1 | ✅ |

---

## 10. Workers y Scripts

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-WRK-001 | **Replicator**: Poll cada 1s eventos `ejercicio-completado` no procesados (batch 100) | §5.2 | ✅ |
| RF-WRK-002 | **Replicator**: Insertar en DuckDB `raw_events` | §5.2 | ✅ |
| RF-WRK-003 | **Replicator**: Actualizar DuckDB `weekly_progress` (INSERT OR REPLACE) | §5.2 | ✅ |
| RF-WRK-004 | **Replicator**: Marcar evento como `processed=true` en PostgreSQL | §5.2 | ✅ |
| RF-WRK-005 | **Replicator**: No marcar como procesado si DuckDB falla (reintento) | §5.2 | ✅ |
| RF-WRK-006 | **Preventive Worker**: Poll cada 2s eventos `fatiga-alta` no procesados | §5.3 | ✅ |
| RF-WRK-007 | **Preventive Worker**: Loggear advertencia y notificar vía notification-service | §5.3 | ✅ |
| RF-WRK-008 | **Weekly Analysis**: Leer weekly_progress de DuckDB, llamar Ollama, guardar en `projections` | §6.1 | ✅ |
| RF-WRK-009 | **Weekly Analysis**: Publicar evento `recomendacion-ajuste` | §6.1 | ✅ |
| RF-WRK-010 | **Daily Inactivity**: Detectar seniors sin tracking en últimos 4 días | §6.2 | ✅ |
| RF-WRK-011 | **Daily Inactivity**: Publicar evento `inactividad-detectada` por cada inactivo | §6.2 | ✅ |
| RF-WRK-012 | **start_all**: Iniciar los 7 servicios con uvicorn, guardar PIDs | §2.2 | ✅ |
| RF-WRK-013 | **stop_all**: Leer PIDs, detener procesos, limpiar puertos 8000–8006 | §2.2 | ✅ |

---

## 11. Shared Library — `seniorvital_shared`

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-SHR-001 | Pool de conexiones asyncpg singleton con sistema de `owner` | — | ✅ |
| RF-SHR-002 | Modelo `HealthProfile` con validación de edad (60–120), peso (30–200), altura (100–250), nivel fitness, metas, restricciones médicas, equipo | §3.2 | ✅ |
| RF-SHR-003 | Validar restricciones médicas contra conjunto permitido (artrosis_rodilla, osteoporosis, hipertensión, dolor_articular, prótesis) | §3.2 | ✅ |
| RF-SHR-004 | Función `publish_event(stream_name, payload)` para insertar en `event_queue` | — | ✅ |

---

## 12. DuckDB — Analítica

| ID | Requisito | SDD Ref | Estado |
|----|-----------|---------|--------|
| RF-DUCK-001 | Crear tabla `raw_events` en DuckDB con event_id, user_id, event_type, payload, ingested_at | §3.3 | ✅ |
| RF-DUCK-002 | Crear tabla `weekly_progress` en DuckDB con avg_rpe, total_exercises, streak_days, projected_level | §3.3 | ✅ |
| RF-DUCK-003 | Replicar eventos desde PostgreSQL a DuckDB en < 1 segundo | AC-DUCK-01 | ✅ |

---

## 13. Criterios de Aceptación — Resumen

| ID | Descripción | Servicio | Estado |
|----|-------------|----------|--------|
| AC-AUTH-01 | Contraseña hasheada con bcrypt | auth-profile | ✅ |
| AC-AUTH-02 | HTTP 400 si role no permitido | auth-profile | ✅ |
| AC-AUTH-03 | caregiver sin linked_senior_id queda NULL | auth-profile | ✅ |
| AC-AUTH-04 | Senior máx. 3 caregivers | auth-profile | ✅ |
| AC-AUTH-05 | Caregiver solo un linked_senior_id | auth-profile | ✅ |
| AC-RTN-02 | Fallback a rutina por defecto si Ollama falla | routines-ai | ✅ |
| AC-RTN-03 | Respetar restricciones médicas | routines-ai | ✅ |
| AC-NOT-01 | Sobrescribir suscripción existente | notification | ✅ |
| AC-NOT-02 | Envío asíncrono (no bloqueante) | notification | ✅ |
| AC-PERS-01 | Escrituras confirmadas en PostgreSQL | shared | ✅ |
| AC-PERS-02 | Profile validado con HealthProfile | auth-profile | ✅ |
| AC-PERS-03 | linked_senior_id solo no nulo cuando role=caregiver | shared | ✅ |
| AC-DASH-01 | Respuesta < 1s para 3 meses de historial | dashboard | ✅ |
| AC-DUCK-01 | Replicación a DuckDB en < 1s | replicator | ✅ |

---

**Leyenda:** ✅ = Implementado y verificado con test | ☐ = Pendiente
