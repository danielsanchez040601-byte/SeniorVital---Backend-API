# 🛠️ Issue S2-04: Tool Calling e Integración con Supabase

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Agentes Inteligentes Modernos  
**Sprint Técnico:** Sprint 2 — Agentes Inteligentes, ReAct y Tool Calling  

---

## 🎯 1. Catálogo de Herramientas del Endpoint `/api/v1/chat`

En el endpoint `/api/v1/chat` se inyectan 7 herramientas activas para el ciclo ReAct:

| Herramienta | Parámetros | Origen de Datos | Propósito Clínico y Operativo |
| :--- | :--- | :--- | :--- |
| `SafetyCheckTool` (`safety_check`) | `user_id: int`, `activity: str` | **PostgreSQL (`users`, `exercises`)** | Obtiene nivel funcional, patologías y valida seguridad biomecánica contra restricciones. |
| `ExerciseCatalogTool` (`exercise_catalog`) | `level: Optional[int]`, `keyword: Optional[str]` | **PostgreSQL (`exercises`)** | Consulta el catálogo geriátrico de ejercicios seguros filtrados por nivel (1-4) o patología. |
| `RAGSearchTool` (`rag_search`) | `query: str` | **Pipeline RAG S1 (`retrieve_with_telemetry`)** | Recupera contraindicaciones con embeddings y pgvector (`clinical_knowledge_embeddings`), reportando telemetría real. |
| `LogHabitTool` (`log_habit`) | `user_id: int`, `habit_type: str`, `value: float` | **PostgreSQL (`habits`)** | Registra hábitos de hidratación (agua en ml) y descanso (horas de sueño). |
| `GetHabitsTool` (`get_habits`) | `user_id: int`, `days: int` | **PostgreSQL (`habits`)** | Recupera historial de hábitos de los últimos N días para seguimiento del coach. |
| `GetProgressTool` (`get_progress`) | `user_id: int`, `weeks: int` | **PostgreSQL (`tracking`, `workout_sessions`)** | Obtiene métricas de cumplimiento y analítica de sesiones de entrenamiento. |
| `GetRoutineTool` (`get_routine`) | `user_id: int` | **PostgreSQL (`routines`)** | Consulta la rutina activa prescrita para el usuario. |

> *Nota sobre herramientas implementadas:* La librería `src/tools/wellness/` incluye adicionalmente `GenerateRoutineTool` (`generate_routine`) para generación algorítmica de planes de entrenamiento; no se inyecta en el ciclo interactivo de `/chat` al estar destinada a servicios de planificación independientes.

---

## 💻 2. Código de Ejecución Asíncrona con Telemetría Real

```python
@tool
async def consultar_base_conocimiento_rag(consulta: str) -> str:
    """Consulta la ontología clínica consumiendo retrieve_with_telemetry."""
    try:
        from src.rag.retriever.retriever import ClinicalRetriever
        retriever = ClinicalRetriever()
        chunks, telemetry = await retriever.retrieve_with_telemetry(consulta, top_k=2)
        # Retorna fragmentos enriquecidos con telemetría post-ejecución
        # (embedding_mode, vector_backend, vector_store_latency_ms)
        ...
    except Exception as e:
        # Contingencia defensiva: reporta el modo degradado real sin asumir estados ideales
        return "[TELEMETRÍA RAG: Modo=IN_MEMORY_FALLBACK, Backend=IN_MEMORY_FALLBACK, Error=True] ..."
```

---

## ⚠️ 3. Manejo de Fallos y Limitaciones Conocidas

1. **Gestión de Contingencias en Red:** Si la conexión hacia Supabase pgvector experimenta latencia o fallo transitorio, la herramienta captura la excepción y conmuta automáticamente a `IN_MEMORY_FALLBACK`, documentando el estado degradado en la telemetría en vez de abortar la ejecución del agente.
2. **Adherencia Clínica Heurística:** La adherencia a las guías geriátricas (OARSI, EWGSOP2) se valida mediante inspección determinista de reglas y palabras clave contraindicadas, sin asumir garantías absolutas de infalibilidad.
3. **Límites de Cuota de Inferencia:** En entornos sin API keys configuradas, el agente activa el motor de razonamiento clínico determinista para garantizar respuestas seguras de baja intensidad.

---

## 🔍 4. Nota de Auditoría Técnica y Dinamismo de Herramientas

* **Tool Calling Autónomo:** El agente evalúa dinámicamente la intención de la consulta mediante el ciclo ReAct y decide si invocar o no herramientas (`safety_check`, `exercise_catalog`, `rag_search`, `log_habit`, `get_habits`, `get_progress`, `get_routine`), erradicando ejecuciones estáticas incondicionales.
* **Validación Automatizada en CI:** Incorporamos al pipeline de GitHub Actions la ejecución explícita de `tests/tools/` respaldada por el contenedor PostgreSQL de CI, certificando de forma continua la selección de herramientas, consultas directas sin herramientas, cadenas multi-tool y tolerancia a fallos.
* **Telemetría de Invocación:** La traza de herramientas ejecutadas se propaga en el campo `tool_chain` / `telemetry.tool_calls` de la respuesta JSON del endpoint `/api/v1/chat`.
* **Estado Final:** ✅ **Completado, desacoplado y listo para validación final.**

