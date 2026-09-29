# Get Progress Tool

Obtiene insights de progreso y resumen de actividad semanal.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `user_id` | int | Sí | ID del usuario |
| `weeks` | int | No | Semanas hacia atrás (default: 4) |

## Retorno

```json
{
  "success": true,
  "data": {
    "insights": [
      {"week": "2026-08-18", "insight": "Mejoró resistencia", "level": 3}
    ],
    "weekly_activity": [
      {"week": "2026-08-18", "sessions": 3}
    ],
    "total_sessions": 12
  },
  "tool_name": "get_progress"
}
```

## Errores

| Condición | Retorno |
|-----------|---------|
| user_id faltante | `success=false, error="user_id required"` |
| Sin datos | `success=true, data=[]` |

## Ejemplos

```json
{"user_id": 1}
{"user_id": 1, "weeks": 2}
```
