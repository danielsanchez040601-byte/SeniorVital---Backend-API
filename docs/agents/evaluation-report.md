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

## Resultados (modo mock)

| Métrica | Valor | Observación |
|---------|-------|-------------|
| **Tool Accuracy** | 1.00 | Tools correctas cuando el agente decide usarlas |
| **Keyword Coverage** | 0.12 | Bajo — respuestas mock genéricas (esperado) |
| **Safety Compliance** | 81% | 16/20 escenarios cumplan nivel de seguridad |
| **React Validity** | 100% | Todos los flujos ReAct son válidos |
| **Tone Match** | 19% | Bajo — respuestas mock no capturan tono (esperado) |
| **Word Count (avg)** | 11 | Respuestas mock cortas |

### Por categoría

| Categoría | Escenarios | Tool Accuracy | Safety |
|-----------|-----------|---------------|--------|
| no_tool | 3 | 1.00 | 100% |
| single_tool | 7 | 1.00 | 86% |
| multi_tool | 4 | 1.00 | 75% |
| memory | 2 | 1.00 | 100% |
| safety | 2 | 1.00 | 50% |
| edge | 2 | 1.00 | 100% |

## Limitaciones identificadas

### 1. Mock responses no reflejan calidad real
**Problema**: Las respuestas mock son genéricas ("Respuesta sobre X. Consulte con un profesional"). No evalúan la calidad real del LLM.
**Propusición**: Ejecutar `--real` contra Ollama para obtener métricas reales de keyword coverage y tone match.

### 2. Respuestas demasiado cortas
**Problema**: El agente genera respuestas de ~11 palabras en promedio. Para un coach wellness, se esperan 50-150 palabras.
**Propusición**: Ajustar el prompt para inducir respuestas más sustanciales. Agregar validación de longitud mínima en el prompt.

### 3. Safety compliance incompleto en escenarios multi-tool
**Problema**: 25% de escenarios multi_tool no cumplieron el nivel de seguridad esperado.
**Propusición**: Agregar instrucción explícita en el prompt: "Si el usuario tiene restricciones médicas, SIEMPRE incluye una advertencia de seguridad en tu respuesta".

### 4. Falta evaluación contra LLM real
**Problema**: No hay resultados reales de phi3:mini. No sabemos si el LLM produce JSON ReAct válido, si sigue el formato, ni si genera respuestas seguras.
**Propusición**: Ejecutar `python scripts/evaluation/run_coach_evaluation.py --real` y documentar resultados.

### 5. Sin detección de alucinaciones
**Problema**: El framework de métricas no verifica si el agente inventa información médica.
**Propusición**: Adaptar `hallucination_flag()` del RAG evaluation para el contexto del coach.

### 6. Sin evaluación de latencia
**Problema**: No se mide tiempo de respuesta por escenario.
**Propusición**: El runner ya captura `elapsed_seconds`. Agregar métricas de percentiles (p50, p95, p99).

## Fortalezas

1. **Arquitectura ReAct sólida**: 100% de flujos válidos en todos los escenarios
2. **Tool calling correcto**: 100% de accuracy en selección de herramientas
3. **Recuperación de errores**: El engine maneja fallos de tools sin crash
4. **Framework de evaluación**: 20 escenarios, 12 métricas, 63 tests automatizados
5. **Memoria funcional**: Retención de contexto en conversaciones multi-turn

## Próximos pasos

| Prioridad | Acción | Esfuerzo |
|-----------|--------|----------|
| Alta | Ejecutar evaluación `--real` contra Ollama | 30 min |
| Alta | Ajustar prompt para respuestas más largas | 1h |
| Media | Agregar validación de safety en multi-tool | 2h |
| Media | Integrar hallucination_flag para wellness | 4h |
| Baja | Métricas de latencia (p50, p95) | 1h |
| Baja | Evaluar con diferentes modelos (llama3, mistral) | 2h |

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
