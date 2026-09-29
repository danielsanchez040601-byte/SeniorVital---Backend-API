# Get Habits Tool

Obtiene el registro de hábitos diarios (agua, sueño) del usuario.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `user_id` | int | Sí | ID del usuario |
| `days` | int | No | Días hacia atrás (default: 7) |

## Retorno

```json
{
  "success": true,
  "data": {
    "habits": [
      {"date": "2026-08-23", "water_glasses": 8, "sleep_hours": 7.5},
      {"date": "2026-08-22", "water_glasses": 6, "sleep_hours": 8.0}
    ],
    "count": 2
  },
  "tool_name": "get_habits"
}
```

## Errores

| Condición | Retorno |
|-----------|---------|
| user_id faltante | `success=false, error="user_id required"` |
| Sin datos | `success=true, data.habits=[], data.count=0` |

## Ejemplos

```json
{"user_id": 1}
{"user_id": 1, "days": 3}
```
