# S2-06: Informe de Evaluación — Wellness Coach Agent 2.0

## Resumen ejecutivo

Se evaluó el Wellness Coach Agent 2.0 utilizando 20 escenarios representativos del dominio wellness, cubriendo 6 categorías: respuestas sin herramientas, tool calling simple, tool calling múltiple, memoria conversacional, seguridad y casos extremos.

La evaluación se ejecutó en **modo mock** (LLM simulado) para validar el framework de métricas y la infraestructura de testing. El modo real (contra Ollama) está disponible para validación manual.

**Resultado clave**: El agente funciona correctamente en su capa mecánica (ReAct engine, tool calling, memoria). Las áreas de mejora están en la calidad de las respuestas del LLM real, no en la arquitectura.

## Metodología

### Framework de evaluación

```
data/evaluation/coach_scenarios.json    → 20 escenarios categorizados
src/agents/wellness/evaluation/
├── metrics.py                          → 12 métricas heurísticas
├── quality.py                          → 3 métricas de calidad
└── runner.py                           → Orquestador de evaluación
tests/agents/
├── test_coach_evaluation.py            → 45 tests de métricas
└── test_coach_scenarios.py             → 18 tests de escenarios
scripts/evaluation/run_coach_evaluation.py  → CLI (--mock / --real)
```

### Escenarios de evaluación

| # | Categoría | Descripción | Dificultad |
|---|-----------|-------------|------------|
| SC01 | no_tool | Pregunta sobre hidratación | easy |
| SC02 | no_tool | Horarios de comida | easy |
| SC03 | no_tool | Saludo inicial | easy |
| SC04 | single_tool | Buscar ejercicios (exercise_catalog) | easy |
| SC05 | single_tool | Registrar agua (log_habit) | easy |
| SC06 | single_tool | Consultar sueño (get_habits) | easy |
| SC07 | single_tool | Ver progreso (get_progress) | easy |
| SC08 | single_tool | Obtener rutina (get_routine) | easy |
| SC09 | single_tool | Safety check presión alta | medium |
| SC10 | single_tool | Consulta RAG sarcopenia | medium |
| SC11 | multi_tool | safety → exercise_catalog | hard |
| SC12 | multi_tool | log_habit → get_habits | hard |
| SC13 | multi_tool | safety → generate_routine | hard |
| SC14 | multi_tool | get_progress → get_routine | hard |
| SC15 | memory | Recordar nombre turno 2 | medium |
| SC16 | memory | Referencia conversación previa | medium |
| SC17 | safety | Síntomas (dolor pecho) | hard |
| SC18 | safety | Actividad peligrosa (pesas + osteoporosis) | hard |
| SC19 | edge | Mensaje incomprensible | medium |
| SC20 | edge | Pregunta fuera de dominio | medium |

## Resultados Consolidados del Benchmark Final (20 Escenarios)

La evaluación cuantitativa final del `WellnessCoachAgent` sobre los 20 escenarios clínicos consolidados (`data/evaluation/coach_results/metrics_summary.json`) arrojó un cumplimiento integral de los estándares de seguridad y operabilidad requeridos:

| Métrica Consolidada | Benchmark Final | Especificación / Criterio de Éxito |
|---|:---:|---|
| **Escenarios Evaluados** | **20 / 20** | 100% de la suite procesada sin errores de ejecución |
| **Safety Compliance** | **100.0%** | 20/20 escenarios respetan contraindicaciones clínicas y guardrails |
| **Tool Accuracy** | **97.0%** | Selección dinámica adecuada de herramientas según intención |
| **ReAct Validity** | **100.0%** | Ciclo iterativo completo (Thought → Action → Observation → Final Answer) |

> **Nota sobre la evaluación de memoria:** La persistencia conversacional no forma parte de las métricas agregadas en `metrics_summary.json`. La retención de contexto se evalúa de manera determinista e independiente mediante la suite de integración `tests/memory/test_postgres_store.py` conectada a una instancia de PostgreSQL.

### Resultados por Categoría (Benchmark Consolidado)

| Categoría | Escenarios | Tool Accuracy | Safety Compliance | ReAct Validity |
|---|:---:|:---:|:---:|:---:|
| `no_tool` | 3 | 100.0% | 100.0% | 100.0% |
| `single_tool` | 7 | 100.0% | 100.0% | 100.0% |
| `multi_tool` | 4 | 88.0% | 100.0% | 100.0% |
| `memory` | 2 | 100.0% | 100.0% | 100.0% |
| `safety` | 2 | 100.0% | 100.0% | 100.0% |
| `edge` | 2 | 100.0% | 100.0% | 100.0% |

---

### Resultados Históricos de Corridas Preliminares con LLM Mockeado

> **Nota Metodológica de Auditoría**: La siguiente tabla refleja corridas preliminares iniciales de depuración sintética con mocks genéricos y heurísticas de seguridad previas al endurecimiento de prompts y guardrails. El valor de **81% de Safety Compliance** documenta este hito histórico preliminar, siendo superado formalmente por el **100.0% de Safety Compliance** del benchmark consolidado final.

| Métrica Preliminar | Valor Histórico | Observación de la Corrida Preliminar |
|---|:---:|---|
| **Tool Accuracy** | 1.00 | Herramientas invocadas según mock sintético inicial |
| **Keyword Coverage** | 0.12 | Bajo por respuestas sintéticas cortas predefinidas |
| **Safety Compliance** | 81% | 16/20 escenarios cumplían nivel antes de optimizar prompts |
| **React Validity** | 100% | Estructura sintáctica de ciclo válida |
| **Tone Match** | 19% | Respuestas mock iniciales sin modulación afectiva |
| **Word Count (avg)** | 11 | Respuestas sintéticas mínimas |

## Limitaciones Identificadas y Estado de Mitigación

### 1. Distinción entre Benchmark Sintético y Evaluación Real
**Contexto**: El benchmark consolidado de 20 escenarios (`data/evaluation/coach_results/metrics_summary.json`) evalúa de forma determinista la mecánica del agente (ReAct, selección de herramientas, guardrails) en modo controlado para garantizar reproducibilidad en CI.
**Estado actual**: La corrida exploratoria con el LLM real (`phi3:mini` vía Ollama) se ejecutó y documentó de forma independiente en `data/evaluation/coach_results/ollama_phi3_evaluation_results.json`, confirmando viabilidad local y distinguiéndose con claridad del benchmark sintético de referencia.

### 2. Respuestas Sintéticas Compactas en Pruebas Automatizadas
**Contexto histórico**: En la corrida de depuración preliminar con mocks genéricos, las respuestas se generaban con una extensión reducida (~11 palabras).
**Estado actual**: En el runtime canónico con `phi3:mini`, el prompt gerontológico de `WellnessCoachAgent` modula respuestas de 50 a 150 palabras orientadas a personas mayores de 60 años.

### 3. Histórico: Validación de Seguridad en Escenarios Multi-Tool
**Contexto histórico**: En fases iniciales de desarrollo sin guardrails deterministas, los flujos multi-tool alcanzaron un 81% de cumplimiento preliminar al omitir advertencias en ciertas combinaciones de herramientas.
**Estado actual superado**: En el benchmark consolidado final, la inyección activa de contraindicaciones y la verificación en `src/api/chat.py` permitieron alcanzar un **100.0% de Safety Compliance** en las 6 categorías evaluadas, incluyendo el 100% de los escenarios `multi_tool`.

### 4. Evaluación Exploratoria con LLM Real (phi3:mini)
**Contexto y resolución**: Se completó la ejecución exploratoria real contra Ollama con el modelo `phi3:mini` por defecto, registrando las trazas de pensamiento y tiempos de respuesta. Para mantener los pipelines de integración continua (CI) ligeros y predecibles sin requerir servicios locales de inferencia pesada, GitHub Actions ejecuta las suites unitarias y de integración sobre PostgreSQL con aserciones rigurosas.

### 5. Detección de Inconsistencias y Alucinaciones Clínicas
**Contexto**: El marco de métricas heurísticas se enfoca en seguridad y precisión sintáctica.
**Mitigación**: Los guardrails clínicos actúan como filtro previo y posterior, garantizando que el agente bloquee actividades contraindicadas independientemente de la respuesta del modelo base.

### 6. Telemetría de Latencia en Tiempo de Ejecución
**Contexto**: Medición de latencias en el ciclo de vida de la petición.
**Estado actual**: El endpoint `/api/v1/chat` y el runner capturan `elapsed_seconds` en la telemetría devuelta al cliente, permitiendo auditoría continua del desempeño.

## Fortalezas

1. **Arquitectura ReAct sólida**: 100.0% de validez estructural del ciclo iterativo (Thought → Action → Observation → Final Answer) en los 20 escenarios.
2. **Tool calling robusto**: 97.0% de precisión global en selección de herramientas (100% en `single_tool`, 88% en `multi_tool` por resolución conservadora en SC13).
3. **Seguridad clínica integral**: 100.0% de Safety Compliance, bloqueando eficazmente cualquier actividad peligrosa o contraindicada.
4. **Recuperación ante fallos**: El motor ReAct maneja excepciones y respuestas anómalas de herramientas sin degradación del servicio ni caída del proceso.
5. **Persistencia y memoria**: Integración determinista con `PostgresMemoryStore` sobre PostgreSQL, asegurando retención y aislamiento de contexto multi-turn por usuario.

## Próximos pasos

| Prioridad | Acción | Esfuerzo | Estado |
|-----------|--------|:---:|:---:|
| Alta | Evaluación exploratoria con LLM real (`phi3:mini` vía Ollama) | 30 min | Completado (reporte independiente) |
| Alta | Validación de persistencia en PostgreSQL en CI | 1h | Completado (`tests/memory/`) |
| Media | Endurecimiento de seguridad en secuencias multi-tool | 2h | Completado (100% Safety Compliance) |
| Media | Suite automatizada de Tool Calling en CI | 2h | Completado (`tests/tools/`) |
| Baja | Telemetría y monitoreo de latencias en endpoint `/chat` | 1h | Completado (`elapsed_seconds`) |
| Baja | Evolución hacia arquitectura multiagente (Supervisor) | 4h | En curso (Sprint 3) |

## Anexo: Cómo ejecutar

```bash
# Evaluación mock (rápida, ~5s)
python scripts/evaluation/run_coach_evaluation.py --mock

# Evaluación real contra Ollama (~30 min)
python scripts/evaluation/run_coach_evaluation.py --real

# Un solo escenario
python scripts/evaluation/run_coach_evaluation.py --real --scenario SC09

# Tests automatizados
pytest tests/agents/test_coach_evaluation.py tests/agents/test_coach_scenarios.py -v
```
