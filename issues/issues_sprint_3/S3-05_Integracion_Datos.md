# 🗄️ Issue S3-05: Seguridad, Persistencia en Supabase y Consultas JSONB

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** Implementado — pendiente de aprobación docente  

---

## 🔒 1. Auditoría de Seguridad y Saneamiento de Credenciales

En cumplimiento estricto de las directrices de seguridad de software:
- **Auditoría Integral de Configuraciones:** Auditamos `src/api/config.py`, `app/config.py`, `tests/tools/conftest.py`, `seniorvital_shared/db.py` y scripts de evaluación.
- **Eliminación de Secretos y Contraseñas Hardcodeadas:** Se erradicaron contraseñas personales o URLs reales de producción que residían como valores por defecto en el código fuente.
- **Carga Estricta desde Entorno:** Todas las credenciales sensibles (`DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`) se cargan exclusivamente mediante `os.getenv(...)`. Purgamos el valor por defecto inseguro de `JWT_SECRET`: en entornos productivos o de staging (`ENV` o `ENVIRONMENT` en `production` o `staging`), el sistema exige de forma mandatoria la variable de entorno arrojando `ValueError` en caso de ausencia, admitiendo únicamente un valor efímero para pruebas locales (`insecure-local-testing-secret-only`) en entornos no productivos.

---

## 💾 2. Consultas Ejecutadas contra Supabase (PostgreSQL / JSONB)

Documentamos las consultas canónicas implementadas para persistencia de sesiones conversacionales, rutinas y analítica:

### 2.1. Persistencia de Sesiones Conversacionales (`conversation_history`)
Permite al `PostgresMemoryStore` persistir los turnos conversacionales con contexto estructurado en columnas JSONB:

```sql
-- Inserción de mensaje con metadatos estructurados
INSERT INTO conversation_history (
    user_id,
    role,
    content,
    metadata,
    created_at
) VALUES (
    $1,                                 -- user_id (VARCHAR / UUID)
    $2,                                 -- 'user' | 'assistant'
    $3,                                 -- texto del mensaje
    $4::jsonb,                          -- {"correlation_id": "...", "agent": "nutrition", "tool_chain": [...]}
    NOW()
);

-- Recuperación cronológica de historial reciente
SELECT 
    role,
    content,
    metadata,
    created_at
FROM conversation_history
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT $2;
```

### 2.2. Registro y Consulta de Rutinas Diarias (`daily_routines`)
Almacena las rutinas prescritas por el coach con su estructura de ejercicios en formato JSONB:

```sql
-- Consulta de rutina activa para una fecha dada
SELECT 
    id,
    senior_id,
    assigned_date,
    status,
    exercises,                          -- JSONB con lista de ejercicios, series, repeticiones
    notes,
    created_at
FROM daily_routines
WHERE senior_id = :user_id 
  AND assigned_date = :target_date
LIMIT 1;

-- Inserción de nueva rutina adaptada
INSERT INTO daily_routines (
    senior_id,
    assigned_date,
    status,
    exercises,
    notes,
    created_at
) VALUES (
    :senior_id,
    :assigned_date,
    'pending',
    :exercises_jsonb::jsonb,
    :notes,
    NOW()
) RETURNING id;
```

### 2.3. Agregación Analítica de Adherencia y Riesgo (`exercise_records`)
Ejecutada por el `AnalyticsAgent` para evaluar la tasa de cumplimiento y la percepción subjetiva de esfuerzo (escala Borg RPE):

```sql
-- Cálculo de adherencia y fatiga en ventana de 14 días
SELECT 
    er.senior_id,
    COALESCE(AVG(er.rpe_score), 0.0) AS avg_rpe,
    COUNT(er.id) AS total_records,
    COUNT(CASE WHEN er.reported_pain != 'Sin Dolor' THEN 1 END) AS pain_incidents,
    COUNT(dr.id) AS completed_routines
FROM exercise_records er
LEFT JOIN daily_routines dr 
       ON dr.senior_id = er.senior_id 
      AND dr.status = 'completed'
      AND dr.assigned_date >= (CURRENT_DATE - INTERVAL '14 days')
WHERE er.senior_id = :user_id
  AND er.completed_at >= (NOW() - INTERVAL '14 days')
GROUP BY er.senior_id;
```

### 2.4. Persistencia de Hábitos Gerontológicos (`daily_habits`)
Permite el seguimiento de hidratación (vasos de agua) y descanso (horas de sueño):

```sql
-- Upsert diario de hábitos
INSERT INTO daily_habits (
    senior_id,
    log_date,
    water_glasses,
    sleep_hours,
    mood,
    created_at
) VALUES (
    :senior_id,
    :log_date,
    :water_glasses,
    :sleep_hours,
    :mood,
    NOW()
)
ON CONFLICT (senior_id, log_date)
DO UPDATE SET
    water_glasses = EXCLUDED.water_glasses,
    sleep_hours = EXCLUDED.sleep_hours,
    mood = EXCLUDED.mood;
```

---

## ⚡ 3. Resiliencia de Pool de Conexiones

- Reutilizamos el pool `asyncpg` compartido a través de `seniorvital_shared.db`.
- Configuramos `statement_cache_size=0` para operar con el pooler PgBouncer en modo transacción (puerto 6543 de Supabase).
- Implementamos captura de desconexiones para que el sistema continúe respondiendo en modo degradado/mock ante caídas temporales de red sin abortar el flujo conversacional.
