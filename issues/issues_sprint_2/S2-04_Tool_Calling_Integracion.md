# 🛠️ Issue S2-04: Tool Calling e Integración con Supabase

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Agentes Inteligentes Modernos  
**Sprint Técnico:** Sprint 2 — Agentes Inteligentes, ReAct y Tool Calling  

---

## 🎯 1. Catálogo de Herramientas Clínicas del Agente

Se implementaron herramientas asíncronas en `app/tools/clinical_tools.py` y `src/tools/wellness/` con desacoplamiento claro y telemetría post-ejecución:

| Herramienta | Parámetros | Origen de Datos | Propósito Clínico y Telemetría |
| :--- | :--- | :--- | :--- |
| `consultar_restricciones_medicas` / `SafetyCheckTool` | `user_id: str` | **Supabase (`senior_profiles` & `exercise_records`)** | Obtiene nivel de movilidad, patologías y promedio de esfuerzo RPE reciente. |
| `consultar_ejercicios_disponibles` / `ExerciseCatalogTool` | `categoria: Optional[str]` | **Supabase (`exercises`)** | Consulta el catálogo geriátrico de ejercicios seguros filtrados por progresión. |
| `consultar_base_conocimiento_rag` / `RAGSearchTool` | `consulta: str` | **Pipeline RAG S1 (`retrieve_with_telemetry`)** | Recupera contraindicaciones con embeddings HuggingFace y vector store (`SUPABASE_PGVECTOR` o `IN_MEMORY_FALLBACK`), reportando telemetría real (`embedding_mode`, `vector_backend`, `latencia_ms`). |
| `registrar_observacion_clinica` / `LogHabitTool` | `user_id: str`, `observacion: str` | **Memoria / Supabase** | Persiste notas de fatiga, dolor o cambios en el estado del paciente. |

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

* **Tool Calling Autónomo:** El agente evalúa dinámicamente la intención de la consulta mediante el ciclo ReAct y decide si invocar o no herramientas (`safety_check`, `exercise_catalog`, `rag_search`, `log_habit`), erradicando ejecuciones estáticas incondicionales.
* **Telemetría de Invocación:** La traza de herramientas ejecutadas se propaga en el campo `telemetry.tool_calls` de la respuesta JSON del endpoint `/api/v1/chat`.
* **Estado Final:** ✅ **Completado, desacoplado y validado en integración.**

