# 🎬 Guion de Demostración Técnica y Defensa Final (Proyecto Integrador)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Asesoría Clínica:** Ing. Julio Matute  
**Proyecto:** SeniorVital 2.0 — Plataforma Multiagente y RAG para Adultos Mayores  
**Entorno de Producción:** [https://seniorvital-backend.onrender.com](https://seniorvital-backend.onrender.com)  

---

## 🎯 1. Objetivos de la Demostración

Demostrar en tiempo real:
1. La **Orquestación Suprema (Supervisor Pattern)** delegando tareas entre agentes especializados.
2. El funcionamiento del **Procesador RAG** con ontología clínica de 10 patologías geriátricas y embeddings de 384 dimensiones.
3. El ciclo **ReAct (Pensamiento $\to$ Acción $\to$ Observación $\to$ Respuesta Final)** con consulta asíncrona a Supabase PostgreSQL.
4. La resiliencia multi-proveedor (**Google AI Studio** como primario y **OpenRouter** como fallback en caliente).
5. El **Modo Cuidador** con semáforo analítico y permisos de solo lectura.

---

## 📋 2. Guion de Pasos para la Ponencia en Vivo

### 🟢 PASO 1: Verificación de Salud y Conectividad Cloud
* **Objetivo:** Demostrar que el backend está 100% operativo en Render y conectado a Supabase PostgreSQL.
* **Comando cURL:**
  ```bash
  curl -X GET "https://seniorvital-backend.onrender.com/" \
       -H "Accept: application/json"
  ```
* **Respuesta Esperada (HTTP 200):**
  ```json
  {
    "status": "healthy",
    "project": "SeniorVital 2.0 API",
    "environment": "production",
    "database": "Supabase PostgreSQL (Pooler 6543)",
    "vector_store": "pgvector (384d)"
  }
  ```

---

### 🧠 PASO 2: "Orquestación Suprema" Multiagente (Consulta Clínica con Dolor)
* **Objetivo:** Evidenciar cómo el `SupervisorOrchestrator` intercepta, delega al `AnalyticsAgent` (SQL/JSONB en Supabase), activa al `MotivationAgent`, ejecuta el ciclo `ReAct` en el `WellnessCoachAgent` con RAG y finalmente audita con `QAArchitectAgent` bajo norma ISO/IEC 25010.
* **Escenario:** Adulto mayor de 68 años con dolor de rodilla que pregunta si puede hacer sentadillas.
* **Comando cURL:**
  ```bash
  curl -X POST "https://seniorvital-backend.onrender.com/api/v1/chat" \
       -H "Content-Type: application/json" \
       -d '{
         "user_id": "1",
         "query": "Tengo 68 años, me duelen las rodillas por osteoartritis. ¿Puedo hacer sentadillas hoy?"
       }'
  ```
* **Trazas de Ejecución A2A Observables en Logs:**
  1. `[Supervisor:trace_id]` Intercepta petición para `user_id=1`.
  2. `[AnalyticsAgent]` Consulta Supabase $\to$ Adherencia: 0%, RPE previo: 4.2/10, Riesgo: `AMBER`.
  3. `[MotivationAgent]` Genera refuerzo empático cálido ("cada paso cuenta").
  4. `[WellnessCoachAgent]` Inicia ReAct:
     * *Thought:* Detecta osteoartritis y queja de dolor.
     * *Action:* Invoca `consultar_restricciones_medicas` y `consultar_base_conocimiento_rag`.
     * *Observation:* Descarta flexión $>90^\circ$ y saltos.
     * *Final Answer:* Recomienda sentadilla parcial en silla (Nivel 1).
  5. `[QAArchitectAgent]` Audita respuesta $\to$ Veredicto: `APPROVED` (0 infracciones).

---

### 📊 PASO 3: Proyección y Analítica Preventiva (Modo Cuidador)
* **Objetivo:** Mostrar la analítica predictiva calculada en Supabase PostgreSQL para el cuidador.
* **Comando cURL:**
  ```bash
  curl -X GET "https://seniorvital-backend.onrender.com/dashboard/progress/1" \
       -H "Accept: application/json"
  ```
* **Respuesta Esperada:**
  ```json
  {
    "senior_id": 1,
    "completion_rate": 75.0,
    "weekly_adherence": [80, 70, 75, 90, 85, 60, 75],
    "avg_rpe": 4.5,
    "fatigue_status": "MODERATE_SAFE",
    "recommendations": "Mantener progresión en Nivel 1 y 2 con pausas activas."
  }
  ```

---

### 🛡️ PASO 4: Prueba de Resiliencia y Fallback en Caliente
* **Objetivo:** Explicar cómo el sistema conmuta automáticamente de Google AI Studio (`gemini-3.6-flash`) a OpenRouter (`openrouter/free` o `google/gemma-4-31b-it:free`) cuando hay picos de demanda o errores HTTP 503/429, manteniendo 0% de interrupción en el servicio.

---

## 🏆 3. Resumen de Criterios Cumplidos para la Evaluación

1. **Cumplimiento Funcional:** 100% de los endpoints de la API operativos.
2. **Ingeniería del Conocimiento:** 10 patologías gerontológicas modeladas con reconocimiento explícito al **Ing. Julio Matute**.
3. **Patrón ReAct & Tool Calling:** Invocación asíncrona real a Supabase PostgreSQL.
4. **Orquestación Multiagente:** Supervisor jerárquico determinista sin bucles infinitos.
5. **Observabilidad:** Métricas estructuradas con `trace_id` y medición de latencias por agente.
