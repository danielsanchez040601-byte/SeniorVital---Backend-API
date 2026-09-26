# Get Routine Tool

Obtiene la rutina activa del día de hoy para un usuario.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `user_id` | int | Sí | ID del usuario |

## Retorno

```json
{
  "success": true,
  "data": {
    "routine": {
      "id": "42",
      "user_id": "1",
      "date": "2026-08-23",
      "exercises": [{"name": "Caminata", "sets": 1, "reps": 10}],
      "warmup": "Rotación de cuello",
      "generated_by": "ollama"
    }
  },
  "tool_name": "get_routine"
}
```

## Errores

| Condición | Retorno |
|-----------|---------|
| user_id faltante | `success=false, error="user_id required"` |
| Sin rutina hoy | `success=false, error="No routine for today"` |

## Ejemplos

```json
{"user_id": 1}
```
