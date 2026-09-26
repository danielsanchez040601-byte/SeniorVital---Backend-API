# Safety Check Tool

Verifica si una actividad es segura dado el perfil médico del usuario.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `user_id` | int | Sí | ID del usuario |
| `activity` | str | Sí | Descripción de la actividad a verificar |

## Retorno

```json
{
  "success": true,
  "data": {
    "safe": false,
    "warnings": [
      "La actividad 'yoga' puede conflicto con: artritis",
      "El usuario tiene restricciones: artritis, hipertension"
    ],
    "restrictions": ["artritis", "hipertension"],
    "conditions": ["artritis"]
  },
  "tool_name": "safety_check"
}
```

## Lógica de evaluación

1. Busca `health_profile.medical_restrictions` del usuario
2. Compara contra `exercises.contraindications` de la BD
3. Si la palabra de restricción aparece en la actividad → warning
4. `safe = true` solo si no hay warnings directos

## Errores

| Condición | Retorno |
|-----------|---------|
| user_id o activity faltan | `success=false, error="user_id and activity required"` |
| Usuario no encontrado | `success=false, error="User not found"` |
| Error de BD | `success=false, error="..."` |

## Ejemplos de llamada

```json
{"user_id": 1, "activity": "yoga para artritis"}
{"user_id": 1, "activity": "caminata ligera"}
{"user_id": 1, "activity": "natación en piscina"}
```
