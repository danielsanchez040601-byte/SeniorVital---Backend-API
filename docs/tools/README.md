# Wellness Tools — Herramientas del Coach Agent 2.0

## Arquitectura

```
WellnessCoachAgent
  └─ ReActEngine
       ├─ observe (parse LLM response)
       ├─ think   (select tool)
       ├─ act     (tool.execute(**args))
       └─ evaluate (tool_result → next iteration or final answer)
```

Todas las herramientas implementan el protocolo `Tool` de `src/tools/__init__.py`:

```python
class Tool(Protocol):
    name: str
    description: str
    async def execute(self, **kwargs) -> ToolResult: ...
    def validate_args(self, **kwargs) -> bool: ...
```

## Catálogo de herramientas

| # | Tool | Tipo | Descripción | Fuente de datos |
|---|------|------|-------------|-----------------|
| T1 | `exercise_catalog` | Lectura | Busca ejercicios por nivel, keyword o contraindicaciones | `exercises` table |
| T2 | `generate_routine` | Escritura | Genera rutina personalizada para el día | LLM + `routines` table |
| T3 | `get_habits` | Lectura | Obtiene registro de agua y sueño | `habits` table |
| T4 | `log_habit` | Escritura | Registra consumo de agua o horas de sueño | `habits` table |
| T5 | `get_progress` | Lectura | Obtiene insights y proyecciones semanales | `projections` + `workout_sessions` |
| T6 | `get_routine` | Lectura | Obtiene la rutina activa del día | `routines` table |
| T7 | `rag_search` | Lectura | Consulta la base de conocimiento RAG | ChromaDB |
| T8 | `safety_check` | Lectura | Verifica contraindicaciones médicas | `users` + `exercises` |

## Flujo de Tool Calling

```
Usuario: "¿Qué ejercicios puedo hacer? Tengo artritis"

ReAct Engine:
  1. LLM → {"thought": "Debo verificar seguridad primero",
             "action": "safety_check",
             "action_input": {"user_id": 1, "activity": "ejercicios"}}
  2. safety_check → {safe: false, warnings: ["artritis detectada"]}
  3. LLM → {"thought": "No es seguro, busco alternativas",
             "action": "exercise_catalog",
             "action_input": {"exclude_contraindications": ["artritis"]}}
  4. exercise_catalog → {exercises: [{name: "Natación"}, ...], count: 2}
  5. LLM → "Con artritis, te recomiendo natación o caminata suave..."
```

## Errores y Fallbacks

| Condición | Comportamiento |
|-----------|---------------|
| Tool no encontrada | `ToolResult(success=False, error="Tool 'X' no disponible")` |
| Tool falla (DB, timeout) | `ToolResult(success=False, error=str(e))` → agente responde gracefully |
| Argumentos inválidos | `ToolResult(success=False, error="... required")` |
| Respuesta vacía del LLM | Fallback: "Disculpa, no pude procesar tu solicitud..." |
| Max iteraciones (3) | Último thought del LLM como respuesta |

## Documentación por herramienta

- [exercise_catalog.md](exercise_catalog.md)
- [generate_routine.md](generate_routine.md)
- [get_habits.md](get_habits.md)
- [log_habit.md](log_habit.md)
- [get_progress.md](get_progress.md)
- [get_routine.md](get_routine.md)
- [rag_search.md](rag_search.md)
- [safety_check.md](safety_check.md)
