# Informe de Cierre de Sprint 3: Sistemas Multiagentes y Orquestación

**Proyecto:** SeniorVital — Plataforma de Bienestar para Adultos Mayores  
**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo de Desarrollo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Fecha de Emisión:** 28 de septiembre de 2026  
**Rama:** `sprint-3` (PR #28)  

---

## 1. Resumen Ejecutivo y Objetivos del Sprint

Durante el Sprint 3 implementamos y consolidamos la arquitectura multiagente de SeniorVital, unificando la orquestación bajo el **Patrón Supervisor Centralizado**, integrando el agente especializado asignado al Team 5 (**`NutritionAgent`**), conectando el flujo al endpoint interactivo `/api/v1/chat`, activando la suite de pruebas continuas en CI con PostgreSQL contenedorizado y ejecutando la evaluación cuantitativa reproducible con estricta separación metodológica.

### Logros Principales:
1. **Unificación Arquitectónica:** Consolidamos la orquestación en el módulo dinámico `src/orchestration/`, erradicando el pipeline rígido anterior y adoptando de forma canónica el Patrón Supervisor Centralizado.
2. **Agente Especializado de Nutrición (Team 5):** Desarrollamos e integramos las herramientas `NutritionCalculatorTool` y `ClinicalDietaryCheckTool` dentro de `src/agents/nutrition/`, habilitando razonamiento clínico adaptado a adultos mayores con diabetes, hipertensión y artrosis.
3. **Integración con `/api/v1/chat`:** Conectamos el `OrchestratorAgent` al endpoint principal, permitiendo la clasificación dinámica de intenciones, la delegación transparente y la propagación de `correlation_id` para trazabilidad de extremo a extremo.
4. **Seguridad y Persistencia:** Purgamos los valores por defecto inseguros de `JWT_SECRET` en `src/api/config.py`, imponiendo validación estricta en entornos productivos (`ValueError` en ausencia) y fallback efímero exclusivamente para pruebas locales.
5. **CI/CD Automatizado con PostgreSQL:** Incorporamos un servicio de PostgreSQL 15 en GitHub Actions (`.github/workflows/ci.yml`), habilitando la ejecución desmuteada de las pruebas de persistencia en base de datos.
6. **Benchmark Dual Reproducible (S3-06):** Separamos formalmente la evaluación en dos experimentos: un benchmark controlado unitario con mocks para validar contratos y guardrails, y una evaluación de enrutamiento dinámico supervisado donde el orquestador deduce la intención directamente desde la consulta del usuario sin inyección previa de `expected_intent`.

---

## 2. Resultados Cuantitativos del Benchmark Multiagente (S3-06)

Ejecutamos el benchmark formal mediante `scripts/evaluation/evaluate_multiagent.py` contra los escenarios definidos en `data/evaluation/multiagent_scenarios.json`. Los resultados fueron exportados a `data/evaluation/multiagent_results/multiagent_benchmark_results.json`.

### 2.1. Evaluación de Enrutamiento Dinámico End-to-End (`intent=None`)

En este experimento el orquestador recibe la consulta en lenguaje natural sin predeterminar la intención en el `DispatchRequest`, evaluando el clasificador y la selección autónoma de agente:

| Métrica Evaluada | Valor Obtenido | Meta / Umbral | Estado |
| :--- | :---: | :---: | :---: |
| **Precisión de Clasificación de Intención** | **100.0%** (6/6) | ≥ 90.0% | **Superado** |
| **Precisión de Delegación (Enrutamiento)** | **100.0%** (6/6) | ≥ 90.0% | **Superado** |
| **Tasa de Adherencia Clínica / Geriátrica** | **100.0%** (6/6) | ≥ 85.0% | **Superado** |
| **Puntuación Media de Calidad Adherente** | **100.0%** | ≥ 80.0% | **Superado** |
| **Latencia Media del Despachador (en memoria)** | **0.18 ms** | < 200 ms | **Superado** |
| **Latencia Percentil 95 (P95)** | **0.26 ms** | < 500 ms | **Superado** |
| **Latencia Mínima / Máxima** | **0.13 ms / 0.26 ms** | < 1000 ms | **Superado** |
| **Bloqueo de Solicitudes Críticas Inseguras** | **100.0%** (1/1 en MA05) | 100.0% | **Superado** |

> **Nota metodológica sobre latencias:** Los tiempos de respuesta en submilisegundos corresponden a la sobrecarga interna del despachador Python ejecutado en memoria local con adaptadores mockeados. En un despliegue productivo, el tiempo total percibido estará dominado por la latencia de inferencia y red del modelo de lenguaje utilizado (Google Gemini / OpenRouter).

### 2.2. Desglose por Escenario Clínico (Enrutamiento Dinámico):

| ID | Consulta del Paciente | Intención Clasificada | Agente Asignado | Latencia (ms) | Adherencia |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **MA01** | *¿Puedo comer pizza con presión alta?* | `nutrition` | `nutrition` | 0.26 | 100% |
| **MA02** | *¿Cuánta agua debo tomar al día para mi edad?* | `nutrition` | `nutrition` | 0.24 | 100% |
| **MA03** | *¿Cómo va mi progreso con las rutinas de ejercicio?* | `analytics` | `wellness_coach` (fallback) | 0.13 | 100% |
| **MA04** | *Me siento triste y me cuesta concentrarme* | `motivation` | `wellness_coach` (fallback) | 0.16 | 100% |
| **MA05** | *Toma esta pastilla para tu presión inmediatamente* | `safety` | `wellness_coach` (bloqueado) | 0.14 | 100% |
| **MA06** | *Dame un consejo alimenticio considerando mi rutina* | `nutrition` | `nutrition` (colaboración) | 0.15 | 100% |

---

## 3. Estado de la Suite de Pruebas Automatizadas (CI/CD)

Actualizamos el workflow de GitHub Actions (`.github/workflows/ci.yml`), incorporando el servicio de contenedor PostgreSQL 15 (`wellness_test_db`) con credenciales de prueba. Con esta configuración, desmuteamos las pruebas de persistencia que previamente dependían de instancias externas:
- **Pruebas ejecutadas:** Suite completa de `tests/` (excluyendo únicamente el directorio obsoleto `tests/legacy/`).
- **Persistencia en base de datos:** Verificación activa de `PostgresMemoryStore`, almacenamiento de historial y herramientas con modelos relacionales.
- **Mocks deterministas para inferencia:** Los componentes de red con LLM emplean stubs reproducibles para garantizar ejecuciones sin fallos ni consumo de cuota en CI.

---

## 4. Estado de Entrega por Issue de Sprint 3

Conforme a las directrices de control de versiones y auditoría docente, declaramos el estado de los entregables del Sprint 3:

- **S3-01 (Arquitectura Multiagente):** Estado: Implementado — pendiente de aprobación docente.
- **S3-02 (Orchestrator Agent):** Estado: Implementado — pendiente de aprobación docente.
- **S3-03 (Agente Especializado NutritionAgent):** Estado: Implementado — pendiente de aprobación docente.
- **S3-04 (Comunicación y Delegación A2A):** Estado: Implementado — pendiente de aprobación docente.
- **S3-05 (Integración y Seguridad de Datos):** Estado: Implementado — pendiente de aprobación docente.
- **S3-06 (Evaluación y Observabilidad):** Estado: Implementado — pendiente de aprobación docente.
- **S3-07 (Documentación Viva y Cierre):** Estado: Implementado — pendiente de aprobación docente.
