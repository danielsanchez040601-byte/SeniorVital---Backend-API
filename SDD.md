**Documento de Especificación Técnica para Desarrollo Autónomo (SDD)**

**Proyecto:** SeniorVital – Plataforma Inteligente de Bienestar para Adultos Mayores
**Versión del Documento:** 1.0
**Modo de uso:** Este documento es la **una fuente de verdad** para el desarrollo. Se podrá utilizar conocimiento externo siempre y cuando complemente o refuerce alguna debilidad u omisión técnica de lo especificado en este documento. El agente OpenCode debe implementar todas las especificaciones en orden topológico de dependencias, generar pruebas automáticas a partir de los criterios de aceptación y no requerir intervención humana adicional.

1.  **Visión general del sistema**

SeniorVital es un sistema backend compuesto por microservicios que comunican síncronamente vía REST (a través de un API Gateway) y asíncronamente mediante una cola de eventos basada en PostgreSQL. El objetivo es gestionar rutinas de ejercicio personalizadas para adultos mayores, con agentes de IA locales (Ollama), persistencia operacional en PostgreSQL (con JSONB) y analítica embebida en DuckDB.

Arquitectura objetivo (entorno local sin contenedores):

Tecnología obligatoria (inferida de los documentos):

*   Lenguaje: Python 3.12+
*   Framework de API: FastAPI (con Uvicorn)
*   Cliente de base de datos: asyncpg (PostgreSQL asíncrono)
*   Cliente HTTP para Ollama: httpx (asíncrono)
*   Analítica: duckdb
*   Almacenamiento de objetos: sistema de archivos local
*   Autenticación: FastAPI Users + JWT (almacenamiento en PostgreSQL)
*   Notificaciones push (web): Web Push API (biblioteca web-push)
*   Estructura de directorios (debe ser generada por el agente):

seniorvital/
├── auth-profile-service/
├── catalog-service/
├── routines-ai-service/
├── tracking-service/
├── dashboard-service/
├── notification-service/
├── gateway/
├── scripts/
│ ├── init\_db.sql
│ ├── start\_all.sh
│ ├── stop\_all.sh
│ ├── replicator.py
│ └── weekly\_analysis.py
├── storage/ # Almacenamiento local de vídeos y fotos
│ ├── videos/
│ └── progress-photos/
├── tests/
└── README.md

1.  **Especificaciones de infraestructura y dependencias**

**2.1. Servicios base (deben estar ejecutándose antes que los microservicios)**

**Componente**

**Puerto**

**Modo de ejecución**

**Verificación**

PostgreSQL

5432

Servicio nativo (Windows)

\`pg\_isready\`

Ollama

11434

Proceso en segundo plano

\`curl http://localhost:11434/api/tags\`

Nota: La comunicación asíncrona se maneja mediante tablas en PostgreSQL.

Especificaciones de configuración (valores predeterminados):

*   PostgreSQL:
*   DB: \`seniorvital\`
*   Usuario: \`sv\_user\`
*   Password: \`sv\_pass\`
*   Host: \`localhost\`
*   Ollama: modelo por defecto \`phi3:mini\` (se descarga la primera vez)
*   Almacenamiento local:
*   Directorios: \`storage/videos/\`, \`storage/progress-photos/\` (creados automáticamente)
*   URL base para vídeos: \`http://localhost:8002/storage/videos/{filename}\`

**2.2. Scripts de automatización**

\`scripts/start\_all.sh\` debe:

*   Iniciar Ollama (\`ollama serve\`).
*   Para cada microservicio, activar entorno virtual y lanzar \`uvicorn main:app --port <puerto> --reload\` en segundo plano, guardando PIDs en \`logs/\`.
*   Esperar 5 segundos entre servicios.
*   Crear los directorios de almacenamiento si no existen.

\`scripts/stop\_all.sh\` debe leer los archivos \`.pid\` y terminar los procesos.

1.  **Especificaciones de persistencia (PostgreSQL + JSONB)**

**3.1. Esquema de base de datos (\`init\_db.sql\`) – incluye nuevas tablas para eventos**

\`\`\`sql

\-- Extensión para UUID

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\-- Tabla users (igual)

CREATE TABLE users (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

email TEXT UNIQUE NOT NULL,

role TEXT NOT NULL CHECK (role IN ('senior', 'caregiver', 'admin')),

profile JSONB NOT NULL,

linked\_senior\_id UUID NULL,

created\_at TIMESTAMP DEFAULT NOW()

);

\-- Tabla tracking (igual)

CREATE TABLE tracking (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

user\_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

completed\_at TIMESTAMP NOT NULL,

exercise\_id TEXT NOT NULL,

sets INT NOT NULL,

reps INT NOT NULL,

rpe INT CHECK (rpe BETWEEN 1 AND 10),

felt\_difficulty TEXT

);

\-- Tabla habits (igual)

CREATE TABLE habits (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

user\_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

date DATE NOT NULL,

water\_glasses INT,

sleep\_hours FLOAT,

UNIQUE(user\_id, date)

);

\-- Tabla routines (rutinas generadas)

CREATE TABLE routines (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

user\_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

date DATE NOT NULL,

exercises JSONB NOT NULL,

warmup JSONB,

active BOOLEAN DEFAULT true

);

\-- Tabla projections (insights del agente preventivo)

CREATE TABLE projections (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

user\_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

week\_start DATE NOT NULL,

insight\_text TEXT,

estimated\_level INT

);

\-- Tabla exercises (catálogo)

CREATE TABLE exercises (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

name TEXT NOT NULL,

level INT CHECK (level BETWEEN 1 AND 4),

contraindications TEXT\[\],

video\_url TEXT -- ahora apunta a ruta local, ej. /storage/videos/abc.mp4

);

\-- NUEVA TABLA: Cola de eventos asíncronos (reemplaza Redis Streams)

CREATE TABLE event\_queue (

id BIGSERIAL PRIMARY KEY,

stream\_name TEXT NOT NULL, -- 'ejercicio-completado', 'fatiga-alta', etc.

payload JSONB NOT NULL,

created\_at TIMESTAMP DEFAULT NOW(),

processed BOOLEAN DEFAULT FALSE,

processed\_at TIMESTAMP

);

\-- Índices para la cola de eventos

CREATE INDEX idx\_event\_queue\_stream\_processed ON event\_queue(stream\_name, processed, created\_at);

\-- Índices originales

CREATE INDEX idx\_tracking\_user\_completed ON tracking(user\_id, completed\_at DESC);

CREATE INDEX idx\_tracking\_exercise ON tracking(exercise\_id);

CREATE INDEX idx\_habits\_user\_date ON habits(user\_id, date);

CREATE INDEX idx\_routines\_user\_date ON routines(user\_id, date);

CREATE INDEX idx\_projection\_user\_week ON projections(user\_id, week\_start);

CREATE INDEX idx\_exercises\_level ON exercises(level);

CREATE INDEX idx\_exercises\_contraindications ON exercises USING GIN(contraindications);

CREATE INDEX idx\_users\_role ON users(role);

**Criterios de aceptación de persistencia:**

*   _AC_−_PERS_−01 Todas las escrituras (POST, PUT, DELETE) deben confirmarse en PostgreSQL con nivel de aislamiento READ COMMITTED.
*   AC−PERS−02_AC_−_PERS_−02 Los datos de profile (JSONB) deben validar el esquema descrito en la sección 3.2 antes de ser insertados.
*   AC−PERS−03_AC_−_PERS_−03 El campo linked\_senior\_id solo puede ser no nulo cuando role = 'caregiver'.

**3.2. Esquema de profile JSONB (validación Pydantic)**

python

from pydantic import BaseModel, Field, validator

from typing import List, Optional

class HealthProfile(BaseModel):

age: int = Field(ge=60, le=120)

weight\_kg: float = Field(ge=30, le=200)

height\_cm: float = Field(ge=100, le=250)

fitness\_level: str = Field(regex="^(principiante|intermedio|avanzado)$")

goals: List\[str\] = Field(min\_items=1)

medical\_restrictions: List\[str\] = Field(default\_factory=list)

equipment: List\[str\] = Field(default\_factory=list)

preferred\_schedule: Optional\[str\] = None

@validator('medical\_restrictions')

def validate\_restrictions(cls, v):

allowed = {"artrosis\_rodilla", "osteoporosis", "hipertensión", "dolor\_articular", "prótesis"}

for item in v:

if item not in allowed:

raise ValueError(f"Restricción no permitida: {item}")

return v

**3.3. Especificación de DuckDB (analítica embebida)**

**Archivo:** seniorvital\_analytics.duckdb (creado en el directorio raíz del proyecto)

**Esquema (creado automáticamente por el replicador):**

sql

CREATE TABLE IF NOT EXISTS raw\_events (

event\_id UUID,

user\_id UUID,

event\_type TEXT,

payload JSON,

ingested\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP

);

CREATE TABLE IF NOT EXISTS weekly\_progress (

user\_id UUID,

week\_start DATE,

avg\_rpe FLOAT,

total\_exercises INT,

streak\_days INT,

projected\_level INT

);

**Criterios de aceptación:**

*   _AC_−_DUCK_−01 El replicador debe insertar en raw\_events cada evento desde la cola PostgreSQL en menos de 1 segundo tras su publicación.
*   AC−DUCK−02_AC_−_DUCK_−02 El servicio dashboard debe poder consultar weekly\_progress y devolver resultados en < 500 ms.

1.  **Especificaciones de microservicios (contratos REST)**

**4.1. API Gateway (puerto 8000)**

El gateway es un proxy FastAPI que redirige según el prefijo de la ruta:

**Ruta**

**Servicio destino**

/auth/\*

auth-profile:8001

/catalog/\*

catalog:8002

/routines/\*

routines-ai:8003

/tracking/\*

tracking:8004

/dashboard/\*

dashboard:8005

/notify/\*

notification:8006

No debe modificar los cuerpos de las peticiones ni respuestas.

**Especificación:**

*   **SPEC-GW-001:** El gateway debe escuchar en 0.0.0.0:8000 y soportar CORS para origen http://localhost:3000 (frontend desarrollo).

**4.2. Servicio auth-profile (puerto 8001)**

**Responsabilidades:** registro, login, gestión de perfiles, roles y vinculación cuidador-senior.

**4.2.1. Endpoints (FastAPI Users estándar)**

**Método**

**Ruta**

**Descripción**

**Contrato**

POST

/auth/register

Registrar nuevo usuario

Request: {email, password, role, profile} (ver SPEC-AUTH-REG)

POST

/auth/login

Login

Request: {email, password} → Response: {access\_token, token\_type}

GET

/auth/me

Perfil del autenticado

Requiere Bearer token

PUT

/auth/profile

Actualizar perfil (solo senior o admin)

Body parcial profile

POST

/auth/link-caregiver

Vincular cuidador a senior (requiere token de senior)

Request: {caregiver\_email}

**SPEC-AUTH-REG (registro):**

*   **Precondición:** email no existente en users.
*   **Postcondición:** Se crea un registro en users con role especificado (senior por defecto). profile validado con HealthProfile.
*   **Criterios de aceptación:**
*   \[AC-AUTH-01\] Contraseña hasheada con bcrypt (FastAPI Users por defecto).
*   \[AC-AUTH-02\] Respuesta HTTP 400 si role no es uno de los permitidos.
*   \[AC-AUTH-03\] Si role = 'caregiver' y linked\_senior\_id no se envía, queda NULL.

**SPEC-AUTH-LINK:**

*   **Precondición:** El usuario autenticado tiene role = 'senior'. El caregiver\_email existe y tiene role = 'caregiver'.
*   **Postcondición:** Se actualiza linked\_senior\_id del cuidador con el ID del senior.
*   **Criterios:**
*   \[AC-AUTH-04\] Un senior solo puede estar vinculado a máximo 3 cuidadores.
*   \[AC-AUTH-05\] Un cuidador puede tener un solo linked\_senior\_id.

**4.3. Servicio catalog (puerto 8002) – modificado para usar almacenamiento local**

**Responsabilidades:** CRUD de ejercicios, subida de vídeos a sistema de archivos local.

**Endpoints (requieren rol admin para escribir):**

**Método**

**Ruta**

**Descripción**

GET

/catalog/exercises

Listar ejercicios (filtros)

POST

/catalog/exercises

Crear nuevo ejercicio

GET

/catalog/exercises/{id}

Obtener detalle

PUT

/catalog/exercises/{id}

Actualizar

DELETE

/catalog/exercises/{id}

Eliminar

POST

/catalog/exercises/{id}/video

Subir vídeo (multipart) a almacenamiento local

GET

/storage/videos/{filename}

**Nuevo endpoint público** para servir vídeos

**SPEC-CAT-001 (Listar ejercicios) – sin cambios**

**SPEC-CAT-002 (Subida de vídeo – adaptada):**

*   Archivo MP4, tamaño máximo 50 MB.
*   Se guarda en ./storage/videos/<uuid>.mp4.
*   La URL resultante será http://localhost:8002/storage/videos/<uuid>.mp4.
*   El campo video\_url de exercises se actualiza con esta URL.

**Criterios de aceptación:** iguales, pero verificando que el archivo se sirve correctamente.

**4.4. Servicio routines-ai (puerto 8003) – sin caché Redis**

**Responsabilidades:** Generar rutinas usando Ollama, almacenar en PostgreSQL (sin caché externa). No se usa Redis.

**Endpoints:**

**Método**

**Ruta**

**Descripción**

POST

/routines/generate

Generar rutina para hoy (o fuerza renovación)

GET

/routines/today

Obtener rutina del día (desde PostgreSQL)

**SPEC-RTN-001 (Generación de rutina):**

*   _Request Body: { "user\_id": "uuid", "force": false }_
*   _Flujo:_

1.  Obtener perfil de users.
2.  Consultar ejercicios seguros desde exercises.
3.  Construir prompt para Ollama.
4.  Llamar a Ollama (mismo prompt).
5.  Parsear JSON.
6.  Guardar en routines (no hay caché en Redis).
7.  **Publicar evento** rutina-generada **insertando un registro en la tabla** event\_queue con stream\_name='rutina-generada' y payload correspondiente.

*   _Criterios de aceptación:_
*   AC−RTN−01_AC_−_RTN_−01 Latencia total < 3 s.
*   AC−RTN−02_AC_−_RTN_−02 Fallback a rutina por defecto si Ollama falla.
*   AC−RTN−03_AC_−_RTN_−03 Respetar restricciones médicas.

**Plantilla de prompt:** igual que original.

**4.5. Servicio tracking (puerto 8004) – usa event\_queue en lugar de Redis**

**Responsabilidades:** Registrar series, publicar eventos a través de event\_queue.

**Endpoints:** iguales (individual y batch).

**SPEC-TRK-001 (Registro individual):**

*   Se inserta en tracking.
*   Se inserta un registro en event\_queue:
*   stream\_name = 'ejercicio-completado'
*   payload = { "user\_id": ..., "exercise\_id": ..., "rpe": ..., "timestamp": ..., "sets": ..., "reps": ... }
*   Si rpe >= 8, se inserta otro evento con stream\_name = 'fatiga-alta'.
*   **Criterios:** mismos tiempos, pero ahora la publicación es síncrona en la misma transacción (o después, pero se garantiza).

**SPEC-TRK-002 (Lote offline):** mismo comportamiento atómico.

**4.6. Servicio dashboard (puerto 8005)**

**Responsabilidades:** Consultas agregadas para el usuario y cuidador, proyecciones.

**Endpoints:**

**Método**

**Ruta**

**Descripción**

GET

/dashboard/progress/{user\_id}

Resumen de progreso (calendario, tendencias RPE, racha)

GET

/dashboard/projection/{user\_id}

Última proyección generada por agente preventivo

GET

/dashboard/insights/{user\_id}

Lista de insights (estancamiento, motivación)

**SPEC-DASH-001 (Progreso):**

*   **Response:**

json

{

"calendar": {"2026-05-30": 3, "2026-05-31": 2}, _// repeticiones totales por día_

"avg\_rpe\_trend": \[4.2, 4.0, 3.8\],

"streak\_days": 5,

"total\_sessions\_week": 4

}

*   **Fuente de datos:** Principalmente PostgreSQL (tablas tracking y routines). DuckDB solo para proyecciones complejas.
*   **Criterio de aceptación:** \[AC-DASH-01\] El tiempo de respuesta para cualquier usuario con hasta 3 meses de historial < 1 segundo.

**SPEC-DASH-002 (Proyección):**

*   **Origen:** Leer de tabla projections para la semana más reciente. Si no existe, devolver null.
*   **Postcondición:** El agente preventivo periódico (sección 6) actualiza esta tabla.

**4.7. Servicio notification (puerto 8006)**

**Responsabilidades:** Envío de notificaciones push vía Web Push API.

**Endpoints:**

**Método**

**Ruta**

**Descripción**

POST

/notify/subscribe

Guardar suscripción push (endpoint, keys)

POST

/notify/send

Enviar notificación a un usuario específico (solo admin/agente)

**SPEC-NOT-001 (Suscripción):**

*   **Request Body:** { "user\_id": "uuid", "subscription": { "endpoint": "...", "keys": {...} } }
*   **Almacenamiento:** Nueva tabla push\_subscriptions (no definida en esquema inicial, debe crearse).

sql

CREATE TABLE push\_subscriptions (

user\_id UUID PRIMARY KEY REFERENCES users(id),

endpoint TEXT NOT NULL,

p256dh TEXT NOT NULL,

auth TEXT NOT NULL

);

*   **Criterio:** \[AC-NOT-01\] Si el usuario ya tenía suscripción, se sobreescribe.
*   **SPEC-NOT-002 (Envío):**
*   **Request:** { "user\_id": "uuid", "title": "Hidratación", "body": "Hora de beber agua" }
*   **Acción:** Usar biblioteca web-push con claves VAPID configuradas en variables de entorno (valores por defecto generados si no existen).
*   **Manejo de errores:** Si el endpoint devuelve 410 (Gone), eliminar suscripción.
*   **Criterio:** \[AC-NOT-02\] No debe bloquear el flujo principal; ejecutar asíncronamente (background task de FastAPI).

1.  **Especificaciones de eventos asíncronos (tabla event\_queue de PostgreSQL)**

**5.1. Tópicos (stream\_name) y payloads**

**stream\_name**

**Producer**

**Consumers**

**Payload JSON**

ejercicio-completado

tracking

replicador, preventive-worker

{ "user\_id": "uuid", "exercise\_id": "string", "rpe": int, "timestamp": "iso", "sets": int, "reps": int }

fatiga-alta

tracking

preventive-worker

{ "user\_id": "uuid", "rpe\_value": int, "exercise\_id": "string" }

rutina-generada

routines-ai

dashboard (invalida caché)

{ "user\_id": "uuid", "routine\_id": "uuid" }

inactividad-detectada

preventive-worker

notification

{ "user\_id": "uuid", "days\_inactive": int }

**Formato de inserción (en cada microservicio productor):**

python

async with db\_pool.acquire() as conn:

await conn.execute(

"INSERT INTO event\_queue (stream\_name, payload) VALUES ($1, $2)",

"ejercicio-completado", json.dumps(payload)

)

**5.2. Consumidor replicador (**scripts/replicator.py**)**

**Responsabilidad:** Leer eventos no procesados de event\_queue (con stream\_name='ejercicio-completado'), actualizar DuckDB y marcar como procesados.

**Especificación:**

*   Bucle infinito: cada 1 segundo consultar:

sql

SELECT id, payload FROM event\_queue

WHERE stream\_name = 'ejercicio-completado' AND processed = FALSE

ORDER BY created\_at LIMIT 100

*   Por cada fila:
*   Insertar en raw\_events de DuckDB.
*   Actualizar weekly\_progress (usando la misma consulta INSERT OR REPLACE).
*   Marcar processed = TRUE y processed\_at = NOW() en PostgreSQL.
*   Tolerancia a fallos: Si falla DuckDB, se loguea pero no se marca como procesado (se reintentará).
*   Criterios: mismos tiempos y logging.

**5.3. Consumidor de fatiga-alta (**scripts/preventive\_worker.py**)**

Similar al replicador, pero escucha stream\_name='fatiga-alta' y realiza acciones inmediatas (llamar a routines-ai, notificar). También debe marcar eventos como procesados.

1.  **Especificaciones de agentes IA periódicos**

**6.1. Worker de análisis semanal (scripts/weekly\_analysis.py)**

*   Ejecución programada (cron o tarea de Windows) cada lunes 2:00 AM.
*   Detecta estancamiento consultando weekly\_progress (DuckDB) o directamente PostgreSQL.
*   Usa Ollama para generar insight y guarda en projections.
*   Publica evento recomendacion-ajuste insertando en event\_queue (aunque no se especifica un consumidor, puede usarse para futuras extensiones).

**6.2. Agente reactivo a inactividad (scripts/daily\_inactivity.py)**

*   Ejecución diaria.
*   Consulta tracking de últimos 4 días.
*   Si inactivo, inserta evento inactividad-detectada en event\_queue para que notification lo consuma.

**Criterios de aceptación:** iguales.

1.  **Especificaciones de calidad no funcionales – sin cambios relevantes**

Se mantienen todas (RNF-USA-01, RNF-FIA-01, RNF-EFI-01, RNF-SEG-01, RNF-SEG-02, RNF-MAN-01). Solo se ajusta que la prueba de offline-first no depende de Redis.

1.  **Información faltante y predeterminados adoptados**

**Sección**

**Carencia**

**Acción tomada**

Autenticación

Duración token JWT

7 días, sin refresh token

Notificaciones push

Claves VAPID

Generación automática en vapid.json

Modelo Ollama

Descarga previa

ollama pull phi3:mini en script de inicio

Logging

Formato

JSON, nivel INFO, rotación diaria en logs/

Variables de entorno

Lista completa

.env.example con: DATABASE\_URL, OLLAMA\_URL, JWT\_SECRET, VAPID\_\*

Pruebas de carga

Usuarios concurrentes

100 usuarios con latencias especificadas

1.  **Instrucciones finales para el agente OpenCode**

**Orden de implementación recomendado (topológico):**

1.  Scripts de infraestructura (init\_db.sql, start\_all.sh, creación de directorios storage/)
2.  Servicio auth-profile
3.  Servicio catalog (incluye el endpoint estático para vídeos)
4.  Servicio tracking
5.  Servicio routines-ai
6.  Servicio dashboard
7.  Servicio notification
8.  Gateway
9.  Scripts replicador y preventive worker (consumen de event\_queue)

**Pruebas:** igual que original, adaptando los tests para verificar la cola PostgreSQL y el almacenamiento local.

**Documentación:** cada microservicio expone /docs. README explica cómo iniciar el sistema sin contenedores.

**Manejo de errores:** mismo formato {"detail": "..."}.

**Entrega final:** código completo, scripts y documentación; ejecutar start\_all.sh y pasar todas las pruebas. No se requiere interacción humana.