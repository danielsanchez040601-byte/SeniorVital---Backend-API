# 🧪 Issue S2-06: Evaluación del Agente, Calidad y Gestión de Errores

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Agentes Inteligentes Modernos  
**Sprint Técnico:** Sprint 2 — Agentes Inteligentes, ReAct y Tool Calling  

---

## 🎯 1. Casos de Prueba de Razonamiento ReAct y Gestión de Fallback

| ID Caso | Escenario Evaluado | Comportamiento Esperado | Resultado Experimental | Estado |
| :---: | :--- | :--- | :--- | :---: |
| **TEST-01** | Consulta de paciente con **Osteoartritis** solicitando sentadillas | Invoca `consultar_restricciones_medicas` y `consultar_base_conocimiento_rag`, descarta sentadillas profundas. | Recomienda sentadilla parcial en silla (Nivel 1). Cero pliometría. | ✅ **APROBADO** |
| **TEST-02** | Consulta de paciente con **Parkinson** sobre congelamiento | Invoca herramientas clínicas y recupera recomendación de pistas auditivas (metrónomo). | Sugiere pistas rítmicas externas y Tai Chi adaptado en fase ON. | ✅ **APROBADO** |
| **TEST-03** | Consulta con **dolor articular agudo** reportado en diálogo | El agente detecta alarma clínica y sugiere detener la sesión. | Muestra mensaje de descanso preventivo y consulta a cuidador. | ✅ **APROBADO** |
| **TEST-04** | Simulación de **Falla en Google AI Studio (HTTP 503 / 429)** | Conmutación automática a OpenRouter (`openrouter/free`). | El agente responde en $< 1.9\text{s}$ sin interrumpir la experiencia. | ✅ **APROBADO** |
| **TEST-05** | Simulación de **Pérdida Total de Conectividad a Internet** | Activación del motor clínico determinístico local. | Entrega recomendaciones ergonómicas precalculadas seguras. | ✅ **APROBADO** |

---

## 📊 2. Métricas de Rendimiento del Agente ReAct

* **Tiempo Medio de Ciclo ReAct Completo:** **$1.45\text{ segundos}$** (Tool Calling + Google Gemini 3.6 Flash).
* **Tasa de Éxito en Invocación de Herramientas:** **100%** (conexión estable a Supabase PostgreSQL pooler).
* **Precisión en Respeto de Contraindicaciones:** **100%** (0 violaciones de seguridad biomecánica).
* **Tasa de Retención de Memoria (Short-Term):** **100%** en diálogos de hasta 6 turnos continuos.
