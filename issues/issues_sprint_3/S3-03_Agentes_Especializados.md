# 👥 Issue S3-03: Agentes Especializados del Ecosistema

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** ✅ APROBADO Y CERRADO TRAS AUDITORÍA DE SPRINT 3  

---

## 📋 1. Catálogo y Matriz de Competencias de los Agentes

| Agente Especializado | Asignación | Entrada Principal | Salida Producida | Tecnologías & Herramientas |
| :--- | :--- | :--- | :--- | :--- |
| **`NutritionAgent`** | **Team 5 (Especializado)** | Consulta nutricional, perfil médico (diabetes, hipertensión, artrosis). | Plan dietético adaptado, cálculo calórico, ingesta hídrica gerontológica. | `NutritionCalculatorTool`, `ClinicalDietaryCheckTool`, ReAct, RAG. |
| **`WellnessCoachAgent`** | Core Platform | Consulta de bienestar, RAG context, restricciones físicas. | Prescripción gerontológica adaptada (Nivel 1 a 4). | LangGraph/ReAct, Gemini, `SafetyCheckTool`, `ExerciseCatalogTool`. |
| **`AnalyticsAgent`** | Soporte Analítico | `senior_id`, histórico de 14 días en Supabase. | Tasa de adherencia, fatiga promedio (RPE Borg), semáforo de riesgo. | SQLAlchemy async, Supabase PostgreSQL (SQL/JSONB). |
| **`MotivationAgent`** | Soporte Afectivo | Nombre del paciente, tasa de adherencia, riesgo clínico. | Mensaje de refuerzo positivo no punitivo (WCAG 2.1 AA). | Heurística empática gerontológica. |
| **`QAArchitectAgent`** | Calidad & Seguridad | Texto de respuesta sin procesar del coach o nutricionista. | Veredicto de aprobación (`APPROVED/SANITIZED`), lista de violaciones. | Filtros determinísticos ISO/IEC 25010 & SWEBOK v4. |

---

## 🥗 2. Detalle y Evidencia del NutritionAgent (Team 5)

La documentación exhaustiva de implementación, herramientas y evidencia de ejecución real del `NutritionAgent` se encuentra registrada en [S3-03_Agente_Especializado.md](./S3-03_Agente_Especializado.md).

### Resumen de Reglas de Negocio Implementadas:
1. **Prevención de Sarcopenia:** Ingesta proteica orientada entre 1.0 y 1.2 g/kg/día con fuentes de alta biodisponibilidad y fácil masticación.
2. **Control Cardiovascular y Renal:** Restricción estricta de sodio (<1500 mg/día) en pacientes hipertensos y sugerencias de dieta DASH.
3. **Control Glucémico:** Fomento de hidratos de carbono complejos con fibra soluble (>25 g/día) y eliminación de azúcares simples en personas con diabetes mellitus.
4. **Hidratación Sistemática:** Cálculo de 30-35 ml/kg/día con pauta de consumo distribuida durante las horas diurnas para prevenir deshidratación asintomática.
