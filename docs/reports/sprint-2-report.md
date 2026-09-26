# Sprint 2 — Wellness Coach Agent 2.0

## Resumen ejecutivo

El Sprint 2 construyó el Wellness Coach Agent 2.0: un agente conversacional cognitivo con memoria persistente, 8 herramientas de bienestar, razonamiento ReAct y un framework de evaluación. El agente evoluciona del generador de rutinas stateless (Sprint 1) a un coach personal que mantiene conversaciones multi-turno, razona sobre el estado del usuario y ejecuta acciones concretas.

**Resultado**: 204/205 tests pasan, 97 tests nuevos, agente funcional con memoria PostgreSQL, tool calling y evaluación mock.

## Sprints completados

### S2-01: Refactorización del agente base

| Campo | Valor |
|-------|-------|
| Issue | #10 |
| Estado | Completado |
| Componentes | `src/agents/wellness/agent.py`, `config.py`, `prompts/routine_builder.py` |
| Tests | 12 |

**Resultado**: WellnessAgent refactorizado con Strangler Fig y feature flag `USE_REFACTORED_AGENT`. Se separaron Database, services, repositories y prompts en módulos independientes.

### S2-02: Coach Agent 2.0 + ReAct engine

| Campo | Valor |
|-------|-------|
| Issue | #11 |
| Estado | Completado |
| Componentes | `coach.py`, `reasoning.py`, `prompts/wellness_coach.py` |
| Tests | 15 (unit + multi-turn) |

**Resultado**: WellnessCoachAgent con ciclo ReAct (observe→think→act), máximo 3 iteraciones, prompt parametrizable y soporte para tool calling.

### S2-03: Memoria conversacional

| Campo | Valor |
|-------|-------|
| Issue | #12 |
| Estado | Completado |
| Componentes | `src/memory/postgres_store.py`, tabla `conversation_history`, wiring en `main.py` |
| Tests | 16 (11 integration + 5 multi-turn) |

**Resultado**: PostgresMemoryStore con asyncpg pool, persistencia en PostgreSQL,endpoint `POST /chat` en routines-ai-service.

### S2-04: Tool Calling

| Campo | Valor |
|-------|-------|
| Issue | #13 |
| Estado | Completado |
| Componentes | `src/tools/wellness/` (8 tools), `docs/tools/` (9 docs) |
| Tests | 38 (integration + unit + multi-tool chain) |

**Resultado**: 8 herramientas implementadas (exercise_catalog, generate_routine, get_habits, log_habit, get_progress, get_routine, rag_search, safety_check). Documentación completa con schemas, parámetros y ejemplos.

### S2-05: Patrón ReAct y flujo de razonamiento

| Campo | Valor |
|-------|-------|
| Issue | #14 |
| Estado | Completado |
| Componentes | `reasoning.py` (refactored), `wellness_coach.py` (REACT_FORMAT_INSTRUCTIONS), `config.py` |
| Tests | 8 nuevos |

**Resultado**: Instrucciones ReAct en system prompt (`{thought, action, action_input}` / `{thought, final_answer}`), system prompt separado, recuperación de errores con `tool_failure_threshold=2`, parser resiliente, log de trazabilidad.

### S2-06: Evaluación del agente

| Campo | Valor |
|-------|-------|
| Issue | #15 |
| Estado | Completado |
| Componentes | `src/agents/wellness/evaluation/`, CLI, 63 tests |
| Tests | 63 (45 métricas + 18 escenarios) |

**Resultado**: Framework de evaluación con 20 escenarios (6 categorías), 12 métricas heurísticas, runner mock/real. Resultados mock: tool_accuracy=1.0, safety=81%, react_validity=100%.

### S2-07: Documentación

| Campo | Valor |
|-------|-------|
| Issue | #16 |
| Estado | Completado |
| Componentes | `docs/reports/sprint-2-report.md`, actualizaciones a docs existentes |

## Métricas consolidadas

| Métrica | Valor |
|---------|-------|
| Tests totales | 204/205 (1 pre-existing failure) |
| Tests nuevos Sprint 2 | 97 |
| Herramientas | 8 |
| Escenarios de evaluación | 20 |
| Métricas de evaluación | 12 |
| Archivos de documentación | 15+ |
| Módulos Python nuevos | 12 |

## Decisiones técnicas clave

| Decisión | Sprint | Alternativa descartada | Justificación |
|----------|--------|----------------------|---------------|
| PostgreSQL para memoria | S2-03 | Redis, SQLite | Reutiliza pool existente, transaccional, escalable |
| ReAct (no CoT) | S2-02 | Chain-of-Thought puro | Permite tool calling explícito y trazabilidad |
| LLM mockeado en tests | S2-04 | Tests contra Ollama | CI rápido (~90s vs ~30min), determinístico |
| tool_failure_threshold=2 | S2-05 | Break inmediato | 1 fallo recoverable, 2+ indica problema sistémico |
| final_answer explícito | S2-05 | action: "" vacío | Reduce ambigüedad del parser |
| System prompt separado | S2-05 | String concatenado | phi3:mini distingue system vs user |
| Mensajes crudos en memoria | S2-03 | Resúmenes | Sin pérdida de información, el LLM decide relevancia |

## Limitaciones conocidas

1. **Sin evaluación contra Ollama real** — Los resultados son con LLM mockeado
2. **Respuestas cortas** — ~11 palabras en mock; ajustar prompt para respuestas más largas
3. **Sin detección de alucinaciones médicas** — El agente puede inventar información de salud
4. **Sin TTL automático en memoria** — El historial crece indefinidamente
5. **Una sesión por usuario** — Sin distinción entre sesiones
6. **phi3:mini es lento** — 100-500s por query en hardware limitado

## Próximos sprints sugeridos

| Prioridad | Sprint | Descripción |
|-----------|--------|-------------|
| Alta | S3-01 | Evaluar contra Ollama real y ajustar prompts |
| Alta | S3-02 | Multi-agent orchestration (agentes A-F) |
| Media | S3-03 | Detección de alucinaciones médicas |
| Media | S3-04 | TTL y limpieza automática de memoria |
| Baja | S3-05 | Evaluación con modelos alternativos (llama3, mistral) |
| Baja | S3-06 | Session management (múltiples sesiones por usuario) |

## Archivos relevantes

| Sprint | Archivos principales |
|--------|---------------------|
| S2-01 | `src/agents/wellness/agent.py`, `config.py` |
| S2-02 | `src/agents/wellness/coach.py`, `reasoning.py` |
| S2-03 | `src/memory/postgres_store.py`, `conversation_history` DDL |
| S2-04 | `src/tools/wellness/` (8 tools), `docs/tools/` (9 docs) |
| S2-05 | `src/agents/wellness/reasoning.py` (refactored), `prompts/wellness_coach.py` |
| S2-06 | `src/agents/wellness/evaluation/`, `tests/agents/test_coach_*.py` |
| S2-07 | `docs/reports/sprint-2-report.md`, `docs/agents/wellness-agent.md` |
