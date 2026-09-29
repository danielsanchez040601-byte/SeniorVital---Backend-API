# Generate Routine Tool

Genera una rutina de ejercicios personalizada para el día de hoy.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `user_id` | int | Sí | ID del usuario |
| `force` | bool | No | Regenerar aunque ya exista (default: false) |

## Retorno

```json
{
  "success": true,
  "data": {
    "routine": {
      "id": "43",
      "user_id": "1",
      "exercises": [{"name": "Caminata", "sets": 2, "reps": 10}],
      "generated_by": "ollama"
    },
    "generated_by": "ollama"
  },
  "tool_name": "generate_routine"
}
```

## Efectos secundarios

- INSERT en tabla `routines`
- Consume LLM (Ollama) — puede tardar 10-300s

## Errores

| Condición | Retorno |
|-----------|---------|
| user_id faltante | `success=false, error="user_id required"` |
| LLM timeout | `success=false, error="timeout..."` |
| Error de BD | `success=false, error="..."` |

## Ejemplos

```json
{"user_id": 1}
{"user_id": 1, "force": true}
```
