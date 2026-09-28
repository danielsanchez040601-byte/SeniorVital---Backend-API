# RAG Search Tool

Consulta la base de conocimiento de bienestar para adultos mayores.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `query` | str | Sí | Pregunta del usuario |
| `macrodomain` | str | No | Dominio: A=Ejercicio, B=Nutrición, C=Cognición, D=Emocional, E=Social, F=Seguridad |
| `k` | int | No | Chunks a recuperar (default: 5) |

## Retorno

```json
{
  "success": true,
  "data": {
    "answer": "La caminata es recomendada para adultos mayores...",
    "sources": ["guia_ejercicio.pdf"],
    "agent": "ExerciseAgent",
    "macrodomain": "A",
    "warnings": []
  },
  "tool_name": "rag_search"
}
```

## Errores

| Condición | Retorno |
|-----------|---------|
| query faltante | `success=false, error="query required"` |
| Pipeline no disponible | `success=false, error="RAG pipeline not available"` |
| Error en ChromaDB | `success=false, error="..."` |

## Ejemplos

```json
{"query": "¿Qué ejercicios puedo hacer con artritis?"}
{"query": "¿Cómo mejorar el sueño?", "macrodomain": "C"}
```
