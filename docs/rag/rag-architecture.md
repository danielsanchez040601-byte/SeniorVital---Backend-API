# 🏛️ Arquitectura del Pipeline RAG

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdenago Nahmens | **Asesoría Clínica:** Ing. Julio Matute  

---

```mermaid
flowchart LR
    Query["Consulta del Paciente / Perfil"] --> Embed["Hugging Face Embeddings (384d)"]
    Embed --> Search["pgvector Cosine Search (Top-K = 3)"]
    Search --> Filter["Filtro de Contraindicaciones"]
    Filter --> Prompt["Prompt Clínico Aumentado"]
    Prompt --> LLM["Google AI Studio (Gemini Flash)"]
    LLM --> Out["Rutina Adaptada Segura"]
```
