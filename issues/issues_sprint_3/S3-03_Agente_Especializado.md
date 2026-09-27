# 🥗 Issue S3-03: Agente Especializado en Nutrición (NutritionAgent — Team 5)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** ✅ APROBADO Y CERRADO TRAS AUDITORÍA DE SPRINT 3  

---

## 🎯 1. Declaración Formal del Agente Especializado

El **NutritionAgent** es el agente especializado asignado y desarrollado por el **Team 5**. Reside en el paquete `src/agents/nutrition/` y está diseñado específicamente para abordar las necesidades metabólicas, nutricionales e hídricas de adultos mayores (+60 años) que conviven con condiciones crónicas comunes en geriatría.

### Arquitectura Interna del NutritionAgent:
- **Agente Principal (`src/agents/nutrition/agent.py`):** Ejecuta un ciclo iterativo ReAct adaptado a nutrición, consultando herramientas de dominio y generando respuestas empáticas, claras y libres de tecnicismos complejos.
- **Herramientas de Cálculo y Verificación (`src/agents/nutrition/tools.py`):**
  1. `NutritionCalculatorTool`:
     - Tasa Metabólica Basal (TMB) calculada mediante la ecuación Mifflin-St Jeor ajustada por edad y sexo.
     - Requerimiento Calórico Diario (Gasto Energético Total con factor de actividad gerontológica 1.2 a 1.4).
     - Rango Proteico Protector: 1.0 a 1.2 g/kg de peso corporal para prevención de sarcopenia y mantenimiento de masa muscular.
     - Ingesta Hídrica Cuantitativa: 30 a 35 ml/kg/día (ajustable por insuficiencia renal o falla cardíaca).
  2. `ClinicalDietaryCheckTool`:
     - Motor de reglas clínicas que evalúa alimentos contra diagnósticos geriátricos:
       - **Hipertensión Arterial:** Alerta y penaliza alimentos con alto contenido de sodio/sal (>400 mg/porción), embutidos y ultraprocesados; promueve minerales reguladores (potasio, magnesio).
       - **Diabetes Mellitus Tipo 2:** Filtra carbohidratos refinados y azúcares simples; promueve fibra soluble y carbohidratos de bajo índice glucémico.
       - **Osteoartritis / Dolor Articular:** Recomienda ácidos grasos omega-3 y fitoquímicos antiinflamatorios.
- **Adaptador al Protocolo del Orquestador (`src/agents/nutrition/adapter.py`):**
  - Implementa el contrato `AgentProtocol`, permitiendo que el `OrchestratorAgent` le delegue solicitudes mediante `AgentRequest` y reciba `AgentResponse`.

---

## 🧪 2. Evidencia de Ejecución Real y Reproducible

Registramos la ejecución real del `NutritionAgent` despachado dinámicamente por el `OrchestratorAgent`:

### Caso de Prueba 1: Consulta Dietética con Hipertensión (Escenario MA01)
* **Entrada (Usuario):** `"¿Puedo comer pizza con presión alta?"`
* **Intención Clasificada por el Supervisor:** `domain="nutrition"`, `confidence=1.0`
* **Agente Despachado:** `NutritionAgent` (Team 5)
* **Herramientas Invocadas:** `["clinical_dietary_check", "nutrition_calculator"]`
* **Respuesta Generada:**
  > *"Para adultos mayores con presión alta, el consumo frecuente de pizza comercial no es recomendado por su elevado contenido de sal y sodio. Si desea consumirla ocasionalmente, opte por masa integral, queso bajo en sodio y vegetales frescos, consultando siempre a su profesional de la salud."*
* **Evaluación Heurística de Adherencia:** 100% (incluye alerta de sal, presión arterial y advertencia clínica).
* **Latencia de Despacho:** 0.67 ms.

### Caso de Prueba 2: Requerimiento Hídrico Gerontológico (Escenario MA02)
* **Entrada (Usuario):** `"¿Cuánta agua debo tomar al día para mi edad?"`
* **Intención Clasificada por el Supervisor:** `domain="nutrition"`, `confidence=1.0`
* **Agente Despachado:** `NutritionAgent` (Team 5)
* **Herramientas Invocadas:** `["nutrition_calculator"]`
* **Respuesta Generada:**
  > *"Para una persona mayor de 60 años, la ingesta general recomendada es de aproximadamente 1.5 a 2 litros de agua al día (entre 6 y 8 vasos), promoviendo la hidratación continua a lo largo del día sin esperar a sentir sed, salvo restricción hídrica prescrita por su médico."*
* **Evaluación Heurística de Adherencia:** 100% (pauta cuantitativa en litros y recomendación preventiva sin sed).
* **Latencia de Despacho:** 0.30 ms.

### Traza JSON de Salida en Benchmark Reproducible:
```json
{
  "scenario_id": "MA01",
  "query": "¿Puedo comer pizza con presión alta?",
  "expected_intent": "nutrition",
  "expected_agent": "nutrition",
  "actual_agent": "nutrition",
  "delegation_correct": true,
  "safety_level": "safe",
  "blocked": false,
  "tool_calls": [
    "clinical_dietary_check",
    "nutrition_calculator"
  ],
  "latency_ms": 0.67,
  "clinical_quality": {
    "clinical_adherence_score": 1.0,
    "is_adherent": true,
    "adherence_checks": [
      "Cobertura de términos clínicos: ['sal', 'presión', 'profesional']",
      "Advertencia sobre sodio y presión arterial presente"
    ]
  }
}
```

---

## 🔒 3. Consideraciones de Seguridad y Ética Gerontológica

1. **No Prescripción Médica:** El agente incluye en todos los prompts la advertencia explícita de que sus sugerencias no reemplazan las indicaciones de médicos, nutricionistas o geriatras tratantes.
2. **Texturas Seguras:** Promueve preparaciones culinarias de fácil masticación y deglución para prevenir riesgos de atragantamiento en pacientes con disfagia leve.
3. **Consistencia Inter-Agente:** En el escenario colaborativo MA06, el `NutritionAgent` recibe el contexto del entrenamiento reportado por el `WellnessCoachAgent` para recomendar reposición hidroelectrolítica adecuada al esfuerzo físico realizado.
