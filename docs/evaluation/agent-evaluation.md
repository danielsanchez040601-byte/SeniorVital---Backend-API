# Evaluación por Agente

## Rendimiento por agente

| Agente | Dominio | Precision@5 | Recall@5 | Keyword Coverage | Detección |
|--------|---------|-------------|----------|------------------|-----------|
| Nutri-Buddy | E | 0.200 | 0.333 | 0.800 | ❌ No detectado |
| Physio-Evaluator | A | 0.000 | 0.000 | 1.000 | ✅ Detectado |
| Exercise Architect | B | 0.200 | 1.000 | 0.750 | ✅ Detectado |
| Context-Adaptor | C | — | — | — | No evaluado |
| Safety Guardian | D | 0.000 | 0.000 | 0.750 | ❌ Detectado como B |
| Mind & Soul | F | 0.000 | 0.000 | 0.500 | ❌ Detectado como B |

## Análisis por agente

### Exercise Architect (B) — Mejor rendimiento

- **Precision**: 0.200 (mejor de todos)
- **Recall**: 1.000 (encontró todos los relevantes)
- **Detección**: Correcta en 100% de las queries
- **Razón**: Dominio con más chunks (182), mejor cobertura semántica

### Nutri-Buddy (E) — Rendimiento medio

- **Precision**: 0.200
- **Recall**: 0.333
- **Detección**: Falló — el pipeline detectó dominio E como no detectado
- **Razón**: Dominio pequeño (13 chunks), pero la respuesta fue correcta

### Physio-Evaluator (A) — Recall bajo

- **Precision**: 0.000
- **Recall**: 0.000
- **Detección**: Correcta
- **Razón**: Los chunks recuperados no coinciden con los ground truth (distancia semántica)

### Safety Guardian (D) — Confusión de dominio

- **Precision**: 0.000
- **Recall**: 0.000
- **Detección**: Incorrecta (detectado como B)
- **Razón**: Dominio muy pequeño (9 chunks), se confunde con B por keywords compartidas

### Mind & Soul (F) — Peor rendimiento

- **Precision**: 0.000
- **Recall**: 0.000
- **Detección**: Incorrecta (detectado como B)
- **Razón**: 101 chunks pero keywords genéricas que se superponen con B

## Problemas transversales

1. **Confusión B↔F**: Ambos dominios comparten keywords de ejercicio y bienestar
2. **Dominios pequeños (D, E)**: Con pocos chunks, la recuperación es menos precisa
3. **Detección por keywords es frágil**: El QueryProcessor usa overlap de keywords que se superpone entre dominios

## Recomendaciones

1. **Mejorar detección de dominio**: Usar embeddings en vez de keywords para clasificación
2. **Agregar contexto al query**: Incluir el nombre del agente en la consulta al vector store
3. **Re-balancear chunks**: Los dominios D y E tienen muy pocos chunks (9 y 13)
4. **Agregar chunks sintéticos**: Para dominios pequeños, generar chunks adicionales

---

## Wellness Coach Agent 2.0 — Evaluación (Sprint 2)

> Ver [reporte completo](../agents/evaluation-report.md) para detalles y limitaciones.

### Framework de evaluación

| Componente | Ubicación | Contenido |
|------------|-----------|-----------|
| Dataset | `data/evaluation/coach_scenarios.json` | 20 escenarios (6 categorías) |
| Métricas | `src/agents/wellness/evaluation/metrics.py` | 12 funciones heurísticas |
| Calidad | `src/agents/wellness/evaluation/quality.py` | 3 funciones (memoria, coherencia, relevancia) |
| Runner | `src/agents/wellness/evaluation/runner.py` | Orquestador mock/real |
| CLI | `scripts/evaluation/run_coach_evaluation.py` | `--mock` / `--real` |

### Escenarios de evaluación

| Categoría | Cantidad | Qué evalúa |
|-----------|----------|------------|
| no_tool | 3 | Respuestas directas sin herramientas |
| single_tool | 7 | Uso correcto de 1 herramienta |
| multi_tool | 4 | Cadenas de 2+ herramientas |
| memory | 2 | Coherencia multi-turn |
| safety | 2 | Detección de riesgos |
| edge | 2 | Mensajes vacíos, fuera de dominio |

### Métricas implementadas

| Métrica | Función | Descripción |
|---------|---------|-------------|
| Tool Selection Accuracy | `tool_selection_accuracy()` | Fracción de tools esperadas llamadas |
| Tool Chain Completeness | `tool_chain_completeness()` | Cadena ejecutada en orden correcto |
| Unnecessary Tool Calls | `unnecessary_tool_calls()` | Tools llamadas que no estaban en expected |
| React Flow Validity | `react_flow_validity()` | Cada paso tiene JSON válido |
| Safety Compliance | `safety_compliance()` | Respuesta cumple nivel de seguridad |
| Language Check | `language_check()` | Respuesta en idioma esperado |
| Tone Check | `tone_check()` | Tono detectado vs esperado |
| Response Length | `response_length_check()` | Longitud razonable |
| Keyword Coverage | `keyword_coverage()` | Fracción de keywords esperadas |
| Memory Retention | `memory_retention()` | Info clave de turnos anteriores |
| Context Coherence | `context_coherence()` | Sin contradicciones entre respuestas |
| Response Relevance | `response_relevance()` | Respuesta relevante al mensaje |

### Resultados (modo mock)

| Métrica | Valor |
|---------|-------|
| Tool Accuracy | 1.00 |
| React Validity | 100% |
| Safety Compliance | 81% |
| Keyword Coverage | 0.12 (mock genérico) |
| Tone Match | 19% (mock genérico) |

### Cómo ejecutar

```bash
# Mock (rápido, ~5s)
python scripts/evaluation/run_coach_evaluation.py --mock

# Real contra Ollama (~30 min)
python scripts/evaluation/run_coach_evaluation.py --real

# Un solo escenario
python scripts/evaluation/run_coach_evaluation.py --real --scenario SC03

# Tests automatizados
pytest tests/agents/test_coach_evaluation.py tests/agents/test_coach_scenarios.py -v
```

### Resultados (modo real — Ollama phi3:mini)

> Evaluación S3-01: 7 escenarios ejecutados contra Ollama real.

| Métrica | Mock | Real | Notas |
|---------|------|------|-------|
| Tool Accuracy | 1.00 | 0.57 | phi3:mini no usa tools de forma confiable |
| React Validity | 100% | 100% | Formato JSON siempre válido |
| Safety Compliance | 81% | 100% | Detecta correctamente riesgos médicos |
| Tone Match | 19% | 71% | Mejoró con patrones expandidos |
| Keyword Coverage | 0.12 | 0.53 | Respuestas más completas que mock |
| Avg Word Count | — | 49 | Dentro del rango esperado (10-500) |

#### Resultados por escenario (real)

| Scenario | Categoría | Tool Acc | Safety | Tone | Keywords | Words | Tiempo |
|----------|-----------|----------|--------|------|----------|-------|--------|
| SC01 (agua) | no_tool | 1.00 | 100% | 100% | 0.75 | 103 | 78s |
| SC02 (cena) | no_tool | 1.00 | 100% | 100% | 0.75 | 47 | 52s |
| SC03 (saludo) | no_tool | 1.00 | 100% | 100% | 0.67 | 10 | 23s |
| SC08 (dolor) | single_tool | 0.00 | 100% | 100% | 0.67 | 55 | 132s |
| SC09 (emergencia) | single_tool | 0.00 | 100% | 0% | 0.50 | 41 | 73s |
| SC15 (multi-tool) | multi_tool | 1.00 | 100% | 0% | 0.00 | 16 | 19s |

#### Hallazgos clave (S3-01)

1. **phi3:mini (3.8B) no sigue confiablemente el formato ReAct**
   - Responde en lenguaje natural en vez de JSON en ~40% de los casos
   - Cuando responde en JSON, el formato es correcto (con `format_json=True`)
   - Limitación fundamental del modelo, no del código

2. **Prompt optimizado mejora el cumplimiento**
   - System prompt reducido de ~300 a ~100 tokens
   - Ejemplos explícitos en el prompt ayudan al modelo
   - `format_json=True` produce JSON sin markdown fences

3. **Safety detection es robusta (100%)**
   - El modelo identifica correctamente situaciones de riesgo
   - Recomienda consultar a profesionales cuando corresponde

4. **Tono inconsistente**
   - Empático en respuestas directas
   - No siempre mantiene tono cautious en escenarios de seguridad
   - Patrones de tone_check mejorados (prioridad a safety tones)

5. **Limitaciones conocidas**
   - Sin evaluación contra Ollama real completa (20 escenarios)
   - Modelo phi3:mini demasiado pequeño para tool calling confiable
   - Mock data falla en tools que necesitan user_id real
   - Una sesión por usuario (sin TTL en memoria)
