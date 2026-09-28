# 🎥 Issue S3-07: Documentación de Demostración, Validación E2E y Cierre Documental

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** Implementado — pendiente de aprobación docente  

---

## 🎬 1. Guion de Demostración del Ecosistema Multiagente (Supervisor Centralizado)

### Escenario 1: Asesoramiento Nutricional con Hipertensión (`NutritionAgent` — Team 5)
* **Consulta:** *"¿Puedo comer pizza con presión alta?"*
* **Flujo Operativo:**
  1. El endpoint `/api/v1/chat` empaqueta la consulta en un `DispatchRequest` con `correlation_id` único.
  2. `OrchestratorAgent` clasifica autónomamente la intención en el dominio `nutrition` mediante análisis de la consulta.
  3. Despacha la solicitud al `NutritionAgent` (Team 5), el cual activa `ClinicalDietaryCheckTool`.
  4. Genera una advertencia sobre el contenido de sal y sodio para hipertensión arterial y formula alternativas adaptadas (vegetales frescos, masa integral y queso bajo en sal).
  5. El auditor de seguridad (`apply_guardrails`) inspecciona la respuesta verificando que no existan prescripciones farmacológicas indebidas.
* **Resultado:** Enrutamiento dinámico supervisado con validación heurística de adherencia clínica y tiempos de respuesta dependientes del proveedor LLM.

### Escenario 2: Dolor Articular y Restricción de Ejercicio (`WellnessCoachAgent`)
* **Consulta:** *"¿Puedo hacer sentadillas si me duelen las rodillas?"*
* **Flujo Operativo:**
  1. `OrchestratorAgent` detecta intención orientada a seguridad física y acondicionamiento.
  2. Despacha al `WellnessCoachAgent`, el cual ejecuta el ciclo iterativo ReAct.
  3. El agente invoca `SafetyCheckTool`, identificando la contraindicación de flexión profunda de rodilla ante dolor articular.
  4. Formula alternativas seguras de bajo impacto (movilidad en silla o extensiones suaves sin carga).
  5. Registra el turno y metadatos en la tabla `conversation_history` de PostgreSQL.

### Escenario 3: Colaboración Inter-Agente (`WorkflowEngine`)
* **Consulta:** *"Dame un consejo alimenticio considerando mi rutina de hoy."*
* **Flujo Operativo:**
  1. `WorkflowEngine` coordina una secuencia de dos pasos sin ciclos:
     - Paso 1: `WellnessCoachAgent` recupera el progreso y las características del esfuerzo realizado.
     - Paso 2: `NutritionAgent` recibe el contexto `{prev.text}` e infiere requerimientos de hidratación y aporte calórico post-ejercicio.
  2. El supervisor consolida la respuesta final unificada hacia el usuario.

---

## 🔬 2. Alcance y Entornos de Validación Técnica

Para asegurar total transparencia en la verificación de los componentes, delimitamos los entornos de prueba aplicados:

1. **Componentes Validados contra PostgreSQL Real:**
   - La persistencia del historial conversacional (`conversation_history`), la gestión del pool `asyncpg` y el almacenamiento en `PostgresMemoryStore`.
   - Las consultas a tablas relacionales (`users`, `exercises`, `habits`, `routines`) ejecutadas por las herramientas del coach y del agente de nutrición.
   - Estos componentes se validan en local y en el pipeline de GitHub Actions gracias al servicio de contenedor `postgres:15` (`wellness_test_db`) configurado en `.github/workflows/ci.yml`.

2. **Componentes Validados mediante Bancos de Pruebas Mockeados:**
   - La clasificación de intenciones y generación textual dependiente de APIs externas de LLM (Google Gemini y OpenRouter), utilizando stubs deterministas para garantizar reproducibilidad sin cuotas de red ni consumo de tokens.
   - El benchmark sintético unitario de sobrecarga interna en memoria (`evaluate_multiagent.py`), cuyos tiempos submilisegundo representan la eficiencia de la máquina de despacho en Python.

---

## 🚀 3. Trazabilidad y Estado de Entrega

1. **Arquitectura:** Patrón Supervisor Centralizado formalizado en `docs/architecture/multiagent-architecture.md` y `docs/orchestration/orchestration-pattern.md`.
2. **Implementación:** `src/orchestration/` como núcleo canónico conectado al endpoint interactivo `/api/v1/chat`.
3. **Agente Especializado:** `NutritionAgent` (Team 5) con herramientas de cálculo nutricional e inspección dietética en `src/agents/nutrition/`.
4. **CI/CD:** Pipeline automatizado con servicio PostgreSQL activo en GitHub Actions ejecutando `pytest tests/ -v --ignore=tests/legacy/`.
5. **Evaluación:** Benchmark dual reproducible registrado en `data/evaluation/multiagent_results/multiagent_benchmark_results.json` con separación de pruebas unitarias y enrutamiento dinámico supervisado.
6. **Estado Global:** Implementado — pendiente de aprobación docente.
