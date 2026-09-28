# Log Habit Tool

Registra un hábito diario (consumo de agua en vasos o horas de sueño).

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `user_id` | int | Sí | ID del usuario |
| `habit_type` | str | Sí | `"water"` (vasos) o `"sleep"` (horas) |
| `value` | float/int | Sí | Valor a registrar |

## Retorno

```json
{
  "success": true,
  "data": {
    "logged": true,
    "date": "2026-08-23",
    "type": "water",
    "value": 8
  },
  "tool_name": "log_habit"
}
```

## Comportamiento

- **UPSERT**: Si ya existe un registro para hoy, actualiza el valor
- `water`: valor entero (vasos), `sleep`: valor decimal (horas)

## Errores

| Condición | Retorno |
|-----------|---------|
| user_id, habit_type o value faltan | `success=false, error="user_id, habit_type, value required"` |
| habit_type inválido | `success=false, error="user_id, habit_type, value required"` |
| Error de BD | `success=false, error="..."` |

## Ejemplos de llamada

```json
{"user_id": 1, "habit_type": "water", "value": 8}
{"user_id": 1, "habit_type": "sleep", "value": 7.5}
```
