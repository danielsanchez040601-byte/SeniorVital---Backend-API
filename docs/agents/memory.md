# Memoria Conversacional — Wellness Coach Agent 2.0

## Visión general

El sistema de memoria conversacional permite al Wellness Coach Agent 2.0 mantener contexto durante interacciones multi-turno con el usuario. Cada mensaje del usuario y del asistente se persiste en PostgreSQL, permitiendo que el agente recuerde información de conversaciones anteriores dentro de la misma sesión.

## Arquitectura

```
┌──────────────────────────────────────────────────────┐
│                 WellnessCoachAgent                    │
│  chat(user_id, message)                              │
│    │                                                 │
│    ├─ 1. memory_store.get_history(user_id, limit=5)  │
│    │       └─ SELECT FROM conversation_history       │
│    │          WHERE user_id = $1                     │
│    │          ORDER BY created_at DESC LIMIT $2      │
│    │                                                 │
│    ├─ 2. prompt_builder.build(history, profile)      │
│    │       └─ Formatea: HISTORIAL RECIENTE:          │
│    │          [Usuario]: ...                         │
│    │          [Coach]: ...                           │
│    │                                                 │
│    ├─ 3. react_engine.run(system, user_prompt)       │
│    │       └─ Ciclo observe→think→act (max 3)        │
│    │                                                 │
│    └─ 4. memory_store.add_message(user + assistant)  │
│            └─ INSERT INTO conversation_history       │
└──────────────────────────────────────────────────────┘
```

## Estrategia de memoria

### Contexto inmediato vs. persistencia

| Tipo | Descripción | Almacenamiento |
|------|-------------|----------------|
| **Contexto inmediato** | Últimos N mensajes de la conversación actual | PostgreSQL (conversation_history) |
| **Persistencia entre sesiones** | Historial completo de conversaciones anteriores | PostgreSQL (mismo backend) |

La distinción es operativa: el prompt builder solo inyecta los últimos `conversation_history_limit` mensajes (default: 5), pero el historial completo persiste para auditoría y análisis futuro.

### Criterios de actualización

| Evento | Acción |
|--------|--------|
| Usuario envía mensaje | `add_message(role="user", content=...)` |
| Agente genera respuesta | `add_message(role="assistant", content=...)` |
| Recuperación de contexto | `get_history(user_id, limit=N)` |
| Limpieza de sesión | `clear_history(user_id)` (manual, no automático) |

### Decisión de diseño: mensajes crudos vs. resúmenes

Se eligió **mensajes crudos** por:
- Simplicidad: sin pipeline de extracción de preferencias
- Reproducibilidad: el historial es exactamente lo que se dijo
- Sin pérdida de información: el LLM decide qué es relevante del contexto
- Densidad de tokens: el prompt builder controla cuánto contexto inyectar

## Esquema de base de datos

```sql
CREATE TABLE conversation_history (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conv_history_user_created
    ON conversation_history(user_id, created_at DESC);
```

**Campos:**
- `user_id`: FK a users (cascade delete: si se borra el usuario, se borra su historial)
- `role`: "user" | "assistant" | "system"
- `content`: Texto plano del mensaje
- `metadata`: JSONB para metadatos extensibles (tool calls, sources, etc.)
- `created_at`: Timestamp UTC para orden cronológico

**Índice:** `(user_id, created_at DESC)` optimiza el patrón de acceso principal: `WHERE user_id = X ORDER BY created_at DESC LIMIT N`.

## Componentes

### Protocolo (`src/memory/__init__.py`)

```python
class MemoryStore(Protocol):
    async def get_history(self, user_id: str, limit: int = 20) -> list[Message]: ...
    async def add_message(self, user_id: str, message: Message) -> None: ...
    async def clear_history(self, user_id: str) -> None: ...
```

### Implementación PostgreSQL (`src/memory/postgres_store.py`)

- `PostgresMemoryStore`: Implementación concreta usando asyncpg pool
- Reutiliza el pool de `seniorvital_shared` (sin duplicación de infraestructura)
- Parser JSONB robusto: maneja strings, dicts y None de asyncpg

### Integración con el agente (`src/agents/wellness/coach.py`)

```python
class WellnessCoachAgent:
    def __init__(self, ..., memory_store: MemoryStore | None = None):
        self._memory = memory_store

    async def chat(self, user_id: int, message: str) -> str:
        # 1. Recuperar historial
        history = await self._memory.get_history(user_id, limit=5)
        # 2. Construir prompt con historial
        # 3. Ejecutar ReAct
        # 4. Guardar mensajes
        await self._memory.add_message(user_id, Message(role="user", ...))
        await self._memory.add_message(user_id, Message(role="assistant", ...))
```

### Wiring en el servicio (`routines-ai-service/main.py`)

```python
async def _get_coach_agent():
    pool = await get_pool()
    memory = PostgresMemoryStore(pool)
    # ... crear agent con memory_store=memory
```

## Limitaciones conocidas

1. **Sin TTL automático**: El historial crece indefinidamente. Opción futura: cleanup periódico o `clear_history()` programado.
2. **Sin resumen**: El prompt inyecta los últimos N mensajes crudos. Conversaciones muy largas pueden exceder el contexto del LLM.
3. **Sin compresión**: Cada turno completo consume tokens. No hay extracción de preferencias ni resumen de sesión.
4. **Una sesión por usuario**: No hay distinción entre sesiones (si el usuario cierre y vuelva a abrir, el historial acumula).

## Tests

### Tests de integración (11 tests)

`tests/memory/test_postgres_store.py`:
- add/get single message
- chronological order
- respect limit
- empty history
- negative limit raises ValueError
- invalid role raises ValueError
- clear_history
- clear_history isolation between users
- metadata persistence
- empty metadata
- multi-user isolation

### Tests multi-turno (5 tests)

`tests/agents/test_coach_agent.py`:
- `test_multi_turn_remembers_user_name`: 2 turnos, verifica que el nombre se recuerda
- `test_multi_turn_5_turnos_coherent`: 5 turnos con contexto acumulado
- `test_multi_turn_history_limited_by_config`: Verifica que el prompt solo incluye N mensajes
- `test_multi_turn_without_memory_is_stateless`: Sin memoria, cada turno es independiente
- `test_multi_turn_system_role_in_history`: Mensajes del sistema se almacenan correctamente

## Métricas

| Métrica | Valor |
|---------|-------|
| Backend | PostgreSQL (asyncpg) |
| Tabla | conversation_history |
| Mensajes por prompt (default) | 5 |
| Overhead por turno | 2 INSERTs (user + assistant) |
| Costo de lectura | 1 SELECT con índice |
| Latencia target | <50ms por operación de memoria |
