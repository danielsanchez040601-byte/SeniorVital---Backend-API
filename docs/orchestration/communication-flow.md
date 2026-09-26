# Protocolo de Comunicación Inter-Agente y Paso de Mensajes (A2A)

## 1. Estructura de Mensajería Inter-Agente

La comunicación entre agentes especializados se fundamenta en un contrato estricto de paso de mensajes sin acoplamiento a librerías propietarias:

```python
class AgentMessage:
    id: str               # Identificador único de mensaje
    correlation_id: str   # Trazabilidad transaccional compartida
    parent_id: str        # Identificador del mensaje emisor
    source: str           # Nombre del agente emisor
    target: str           # Nombre del agente receptor
    message_type: str     # request | response | alert | audit
    payload: dict         # Datos estructurados del dominio
    timestamp: str        # Marca de tiempo ISO-8601 UTC
```

## 2. Flujo de Ejecución y Paso de Parámetros

```mermaid
sequenceDiagram
    autonumber
    actor U as Adulto Mayor / Cuidador
    participant API as FastAPI Router (/api/v1/chat)
    participant Sup as Supervisor Orchestrator
    participant Ana as AnalyticsAgent (Supabase)
    participant Mot as MotivationAgent
    participant Coach as WellnessCoachAgent
    participant QA as QAArchitectAgent

    U->>API: POST /chat (user_id, query)
    API->>Sup: orchestrate_request(user_id, query)
    
    Note over Sup,Ana: 1. Inspección de Progresión
    Sup->>Ana: analyze_patient_progression(user_id)
    Ana-->>Sup: {adherence: 80%, avg_rpe: 4.2, risk: GREEN}

    Note over Sup,Mot: 2. Refuerzo Empático
    Sup->>Mot: generate_encouragement(user, adherence, risk)
    Mot-->>Sup: {motivational_message, tone: WCAG AA}

    Note over Sup,Coach: 3. Razonamiento ReAct + RAG
    Sup->>Coach: execute_react_cycle(user_id, query)
    Coach-->>Sup: {response, tool_trace, elapsed_time}

    Note over Sup,QA: 4. Auditoría de Seguridad (ISO 25010)
    Sup->>QA: audit_response(raw_response)
    QA-->>Sup: {is_approved: true, violations: []}

    Sup-->>API: Payload Consolidado con Telemetría
    API-->>U: Respuesta amigable + métricas de progreso
```

## 3. Tolerancia a Fallos y Degrado Agraciado

- **Caída de Conexión a Supabase:** Si el pool asíncrono hacia PostgreSQL no responde en el tiempo límite, `AnalyticsAgent` retorna métricas históricas conservadoras por omisión, sin abortar el flujo motivacional ni conversacional.
- **Fallo del Modelo de Inferencia:** Si Google AI Studio retorna un código 429 o 503, el pipeline conmuta hacia el pool de OpenRouter, o en última instancia al motor clínico determinista de RAG, preservando la continuidad del servicio.
- **Violación Detectada por QA:** Si la respuesta generada menciona fármacos o prescripciones de impacto, `QAArchitectAgent` bloquea el texto crudo y el orquestador sustituye la respuesta por una recomendación preventiva sanitizada.
