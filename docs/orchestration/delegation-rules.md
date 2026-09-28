# Reglas de Delegación y Clasificación de Intenciones

## 1. Clasificación Híbrida de Intención

El Orchestrator Agent implementa una estrategia de clasificación en dos etapas:

1. **Heurística Rápida por Palabras Clave de Dominio:**
   - Dominio **Nutrition**: términos como *comer, dieta, alimento, calorías, agua, hidratación, desayuno, cena, proteína*.
   - Dominio **Analytics**: términos como *progreso, avance, fatiga, RPE, esfuerzo, historial, adherencia, reporte*.
   - Dominio **Motivation**: consultas orientadas al estado anímico, desánimo, bienvenida, felicitación o acompañamiento.
   - Dominio **Safety / Critical**: términos de alerta biomecánica o médica (*dolor punzante, taquicardia, mareo, vértigo, caída*).
   - Dominio **General Wellness / Prescripción**: consultas de movilidad articular, rutinas diarias, dosificación de ejercicios en silla.

2. **Clasificación Asistida por LLM con Fallback:**
   - En casos ambiguos donde ninguna regla de palabras clave supere el umbral de confianza, se invoca un prompt conciso de categorización de intenciones hacia el LLM.
   - Si la inferencia de intención falla o experimenta timeout, el orquestador delega por defecto al agente general (`WellnessCoachAgent`), garantizando atención ininterrumpida.

## 2. Matriz de Especialización de Agentes

| Agente Especializado | Responsabilidad Primaria | Almacén de Datos | Política de Seguridad |
| :--- | :--- | :--- | :--- |
| `WellnessCoachAgent` | Prescripción motriz, adaptación funcional y razonamiento ReAct. | Supabase (`senior_profiles`, `exercises`, `pgvector`). | Bloquea ejercicios axiales o pliométricos. |
| `NutritionAgent` | Pautas de hidratación y soporte dietético geriátrico no farmacológico. | Pipeline RAG (`clinical_knowledge`). | Prohíbe suplementos no indicados y dietas restrictivas extremas. |
| `AnalyticsAgent` | Cálculo de adherencia, RPE acumulado y alerta de estancamiento. | Supabase PostgreSQL (`daily_routines`, `exercise_records`). | Agregaciones asíncronas no bloqueantes en solo lectura. |
| `MotivationAgent` | Soporte psicoemocional, refuerzo de constancia y empoderamiento. | Parámetros de sesión y nivel de riesgo. | Pautas WCAG 2.1 AA, tono empático y respetuoso. |
| `QAArchitectAgent` | Auditoría de guardrails de calidad y cumplimiento de normativas. | Diccionarios deterministas de términos clínicos y biomecánicos. | Bloqueo activo de prescripciones lesionales y fármacos. |
