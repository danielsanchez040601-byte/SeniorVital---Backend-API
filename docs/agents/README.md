# Agentes — Documentación

## Wellness Coach Agent 2.0

El agente principal del sistema. Un coach conversacional cognitivo con memoria, herramientas y razonamiento ReAct.

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura del agente](wellness-agent.md) | Componentes, flujo ReAct, herramientas, decisiones de diseño |
| [Memoria conversacional](memory.md) | Estrategia, esquema BD, integración con el agente |
| [Evaluación del agente](evaluation-report.md) | Resultados de evaluación, limitaciones, mejoras |

### Componentes

```
src/agents/wellness/
├── agent.py              # WellnessAgent (base, S2-01)
├── coach.py              # WellnessCoachAgent (S2-02)
├── reasoning.py          # ReActEngine (S2-02, S2-05)
├── config.py             # WellnessConfig
├── evaluation/           # Framework de evaluación (S2-06)
│   ├── metrics.py        # 12 métricas heurísticas
│   ├── quality.py        # Calidad: memoria, coherencia, relevancia
│   └── runner.py         # Orquestador de evaluación
└── prompts/
    ├── routine_builder.py    # RoutinePromptBuilder (S2-01)
    └── wellness_coach.py     # WellnessCoachPromptBuilder (S2-02)
```

## Herramientas

8 herramientas de bienestar que el agente puede invocar.

| Documento | Descripción |
|-----------|-------------|
| [Catálogo de herramientas](../tools/README.md) | Lista completa con schemas y parámetros |
| [exercise_catalog](../tools/exercise_catalog.md) | Búsqueda de ejercicios por nivel/tipo |
| [generate_routine](../tools/generate_routine.md) | Generación de rutinas personalizadas |
| [get_habits](../tools/get_habits.md) | Consulta de hábitos (agua, sueño) |
| [get_progress](../tools/get_progress.md) | Insights y proyecciones de progreso |
| [get_routine](../tools/get_routine.md) | Rutina activa del día |
| [log_habit](../tools/log_habit.md) | Registro de hábitos |
| [rag_search](../tools/rag_search.md) | Consulta a base de conocimiento |
| [safety_check](../tools/safety_check.md) | Verificación de contraindicaciones |

## Evaluación

| Documento | Descripción |
|-----------|-------------|
| [Evaluación del Coach Agent](evaluation-report.md) | 20 escenarios, 12 métricas, resultados |
| [Evaluación por agente (RAG)](../evaluation/agent-evaluation.md) | RAG: precision, recall, keyword coverage |
| [Métricas de evaluación](../evaluation/retrieval-metrics.md) | Precision@k, Recall@k, MRR, Hit Rate |
| [Calidad de respuesta](../evaluation/response-quality.md) | Keyword coverage, alucinaciones, citas |

## Issues del Sprint 2

| Sprint | Issue | Descripción | Estado |
|--------|-------|-------------|--------|
| S2-01 | #10 | Refactorización del agente base | Completado |
| S2-02 | #11 | Coach Agent 2.0 + ReAct | Completado |
| S2-03 | #12 | Memoria conversacional | Completado |
| S2-04 | #13 | Tool Calling (8 herramientas) | Completado |
| S2-05 | #14 | Patrón ReAct y flujo de razonamiento | Completado |
| S2-06 | #15 | Evaluación del agente | Completado |
| S2-07 | #16 | Documentación | Completado |
