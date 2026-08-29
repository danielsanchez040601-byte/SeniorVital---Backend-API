# 🛠️ Issue S2-04: Tool Calling e Integración con Supabase

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Agentes Inteligentes Modernos  
**Sprint Técnico:** Sprint 2 — Agentes Inteligentes, ReAct y Tool Calling  

---

## 🎯 1. Catálogo de Herramientas Clínicas del Agente

Se implementaron cuatro herramientas asíncronas en `app/tools/clinical_tools.py` mediante el decorador `@tool` de LangChain:

| Herramienta | Parámetros | Origen de Datos | Propósito Clínico |
| :--- | :--- | :--- | :--- |
| `consultar_restricciones_medicas` | `user_id: str` | **Supabase (`senior_profiles` & `exercise_records`)** | Obtiene nivel de movilidad, patologías y promedio de esfuerzo RPE reciente. |
| `consultar_ejercicios_disponibles` | `categoria: Optional[str]` | **Supabase (`exercises`)** | Consulta el catálogo geriátrico de ejercicios seguros filtrados por categoría. |
| `consultar_base_conocimiento_rag` | `consulta: str` | **RAG Processor (`clinical_knowledge`)** | Recupera contraindicaciones y evidencia médica con Hugging Face embeddings. |
| `registrar_observacion_clinica` | `user_id: str`, `observacion: str` | **Memoria / Supabase** | Persiste notas de fatiga, dolor o cambios en el estado del paciente. |

---

## 💻 2. Código de Ejecución Asíncrona con SQLAlchemy Pooler

```python
@tool
async def consultar_restricciones_medicas(user_id: str) -> str:
    """Consulta perfil clínico y registros de fatiga RPE en Supabase."""
    async with async_session_factory() as session:
        query = select(SeniorProfile).filter(SeniorProfile.user_id == uid)
        result = await session.execute(query)
        profile = result.scalars().first()
        # Retorna string enriquecido con limitaciones y patologías
```
