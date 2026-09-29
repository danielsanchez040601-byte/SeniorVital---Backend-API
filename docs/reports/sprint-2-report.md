# Sprint 2 — Wellness Coach Agent 2.0

## Resumen ejecutivo

Durante el Sprint 2 desarrollamos y consolidamos el Wellness Coach Agent 2.0: un agente conversacional cognitivo dotado de memoria persistente sobre PostgreSQL, 7 herramientas clínicas y de seguimiento inyectadas en el endpoint `/api/v1/chat`, razonamiento ReAct y un framework de evaluación cuantitativa de 20 escenarios. El agente evoluciona desde el generador de rutinas stateless del Sprint 1 hacia un coach interactivo que mantiene conversaciones multi-turno, razona sobre el estado de salud del adulto mayor y ejecuta acciones seguras y contextualizadas.

**Resultado**: Suite de pruebas completa integrada en CI (validando agentes, endpoint de chat, pipeline RAG, memoria conversacional en PostgreSQL y herramientas), agente funcional con `PostgresMemoryStore`, tool calling dinámico y evaluación reproducible sobre 20 escenarios clínicos.

## Sprints completados

### S2-01: Refactorización del agente base

| Campo | Valor |
|-------|-------|
| Issue | #10 |
| Estado | Completado |
| Componentes | `src/agents/wellness/agent.py`, `config.py`, `prompts/routine_builder.py` |
| Tests | 12 |

**Resultado**: WellnessAgent refactorizado mediante patrón Strangler Fig. Se separaron la capa de base de datos, servicios, repositorios y prompts en módulos independientes orientados a objetos en `src/`.

### S2-02: Coach Agent 2.0 + ReAct engine

| Campo | Valor |
|-------|-------|
| Issue | #11 |
| Estado | Completado |
| Componentes | `src/agents/wellness/coach.py`, `src/agents/wellness/reasoning.py`, `prompts/wellness_coach.py`, proxy de compatibilidad en `app/agents/wellness_coach.py` |
| Tests | 15 (unit + multi-turn) |

**Resultado**: `WellnessCoachAgent` con herencia directa de `WellnessAgent`, ciclo ReAct (`observe → think → act`), máximo 3 iteraciones, prompt parametrizable, soporte para tool calling y cálculo corregido de `elapsed_time` en el adaptador de compatibilidad.

### S2-03: Memoria conversacional

| Campo | Valor |
|-------|-------|
| Issue | #12 |
| Estado | Completado |
| Componentes | `src/memory/postgres_store.py`, tabla `conversation_history`, wiring en `src/api/chat.py` |
| Tests | 11 (integración y persistencia multi-turno en `tests/memory/`) |

**Resultado**: `PostgresMemoryStore` conectado al pool asíncrono de PostgreSQL con retención y recuperación cronológica de contexto histórico. Se incorporó la suite `tests/memory/` en GitHub Actions respaldada por un servicio PostgreSQL contenedorizado en el runner de CI para validar guardar → recuperar → conservar contexto.

### S2-04: Tool Calling

| Campo | Valor |
|-------|-------|
| Issue | #13 |
| Estado | Completado |
| Componentes | `src/tools/wellness/`, inyección de 7 herramientas en `/api/v1/chat`, documentación en `docs/tools/` |
| Tests | 39 (integración, selección, consultas sin herramientas, cadenas multi-tool y recuperación ante fallos en `tests/tools/`) |

**Resultado**: Selección dinámica de herramientas bajo el ciclo ReAct. Se incorporó la suite `tests/tools/` en CI para certificar automáticamente la selección de herramientas, consultas directas sin herramientas, encadenamiento multi-tool y resiliencia ante excepciones. En `/api/v1/chat` se inyectan 7 herramientas activas (`SafetyCheckTool`, `ExerciseCatalogTool`, `RAGSearchTool`, `LogHabitTool`, `GetHabitsTool`, `GetProgressTool`, `GetRoutineTool`), preservando `GenerateRoutineTool` a nivel de librería de servicios.

### S2-05: Patrón ReAct y flujo de razonamiento

| Campo | Valor |
|-------|-------|
| Issue | #14 |
| Estado | Completado |
| Componentes | `src/agents/wellness/reasoning.py`, `prompts/wellness_coach.py`, `config.py` |
| Tests | 8 nuevos |

**Resultado**: Formato estructurado ReAct (`{thought, action, action_input}` y `{thought, final_answer}`), recuperación ante fallos con umbral configurable (`tool_failure_threshold=2`), parser tolerante a variaciones de formato y registro detallado de trazabilidad en cada paso.

### S2-06: Evaluación del agente

| Campo | Valor |
|-------|-------|
| Issue | #15 |
| Estado | Completado |
| Componentes | `src/agents/wellness/evaluation/`, `scripts/evaluation/run_coach_evaluation.py`, `data/evaluation/coach_results/` |
| Tests | 63 (45 métricas unitarias + 18 escenarios) |

**Resultado**: Evaluación cuantitativa del agente sobre la suite oficial de 20 escenarios clínicos geriátricos (`data/evaluation/coach_results/metrics_summary.json`):
- **Escenarios evaluados:** 20/20 procesados sin errores
- **Safety Compliance:** 100.0% (respeto absoluto de restricciones médicas y ausencia de prescripciones no autorizadas)
- **Tool Accuracy:** 97.0% (selección dinámica de herramientas según intención clínica)
- **ReAct Validity:** 100.0% (formato sintáctico y lógico del ciclo ReAct)

> *Aclaración metodológica:* La retención de memoria conversacional no se computa como métrica agregada en `metrics_summary.json`, sino que se valida de manera determinista e independiente en la suite de integración `tests/memory/test_postgres_store.py` sobre PostgreSQL. Corridas históricas preliminares que reportaron 81% de Safety Compliance corresponden a etapas tempranas de depuración con mocks estáticos.

### S2-07: Consolidación Arquitectónica y Documentación

| Campo | Valor |
|-------|-------|
| Issue | #16 |
| Estado | Completado |
| Componentes | `src/api/chat.py`, `src/agents/wellness/coach.py`, `src/services/llm.py`, `docs/reports/sprint-2-report.md`, `README.md` |

**Resultado**: Documentación y código alineados exactamente con la arquitectura actualmente implementada:
- **Runtime Canónico:** Definido en `src/agents/wellness/` con `WellnessCoachAgent` como punto único de verdad.
- **Motor de Razonamiento:** `ReActEngine` gestionando iteraciones, observación de herramientas y final_answer.
- **Almacén de Memoria:** `PostgresMemoryStore` integrado en el endpoint `/api/v1/chat` con persistencia en `conversation_history`.
- **Servicio de Inferencia LLM:** `LLMService` basado en `OllamaClient`, configurado con `OLLAMA_MODEL` en `phi3:mini` por defecto (`http://localhost:11434`) mediante `WellnessConfig`.
- **Herramientas en Endpoint:** 7 herramientas activamente inyectadas en `/api/v1/chat` (`SafetyCheckTool`, `ExerciseCatalogTool`, `RAGSearchTool`, `LogHabitTool`, `GetHabitsTool`, `GetProgressTool`, `GetRoutineTool`).

## Métricas consolidadas

| Métrica | Valor Verificado | Observación |
|---------|:---:|-------------|
| Escenarios clínicos evaluados | 20 / 20 | Suite completa procesada en `metrics_summary.json` |
| Safety Compliance | 100.0% | 20/20 escenarios conformes a normas de seguridad |
| Tool Selection Accuracy | 97.0% | Invocación dinámica de herramientas |
| ReAct Validity | 100.0% | Formato y secuencia válidos de ciclo ReAct |
| Herramientas inyectadas en `/chat` | 7 | Herramientas clínicas y de seguimiento activas |
| Herramientas totales implementadas | 8 | Incluye `GenerateRoutineTool` a nivel de librería |
| Modelo LLM por defecto | `phi3:mini` | Servido localmente mediante `OllamaClient` |
| Almacén de memoria conversacional | PostgreSQL | `PostgresMemoryStore` validado con tests en CI |

## Decisiones técnicas clave

| Decisión | Sprint | Alternativa descartada | Justificación |
|----------|:---:|----------------------|---------------|
| PostgreSQL para memoria | S2-03 | Redis, SQLite, memoria RAM | Reutiliza pool asíncrono existente, transaccional y persistente por usuario |
| ReAct (no CoT puro) | S2-02 | Chain-of-Thought sin herramientas | Permite tool calling explícito, verificación de contraindicaciones y trazabilidad |
| Inferencia local con Ollama | S2-02 | Dependencia exclusiva de API en la nube | Permite despliegue autocontenido con `phi3:mini`, privacidad de datos clínicos y control de latencia |
| Mocks deterministas en CI | S2-04 | Dependencia de servicio LLM activo en runner | Pruebas de CI rápidas, determinísticas y sin fallos por conectividad externa |
