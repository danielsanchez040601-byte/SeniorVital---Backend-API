# Exercise Catalog Tool

Busca ejercicios del catálogo por nivel funcional, palabra clave o exclusiones de contraindicaciones.

## Parámetros

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `level` | int | No | Nivel funcional: 1=frágil, 2=activo, 3=muy activo, 4=deportista |
| `keyword` | str | No | Palabra clave para buscar en nombre/descripción |
| `exclude_contraindications` | list[str] | No | Contraindicaciones a excluir (ej: `["artritis"]`) |

## Retorno

```json
{
  "success": true,
  "data": {
    "exercises": [
      {
        "id": 1,
        "name": "Caminata ligera",
        "description": "Camina a paso suave por 10 minutos",
        "level": 1,
        "contraindications": "",
        "video_url": ""
      }
    ],
    "count": 1
  },
  "tool_name": "exercise_catalog"
}
```

## Errores

| Condición | Retorno |
|-----------|---------|
| level fuera de rango (1-4) | `success=false, error="Invalid arguments"` |
| Sin resultados | `success=true, data.exercises=[], data.count=0` |
| Error de BD | `success=false, error="..."` |

## Ejemplos de llamada

```json
{"level": 1}
{"keyword": "yoga"}
{"exclude_contraindications": ["artritis", "hipertension"]}
{"level": 2, "keyword": "estiramiento"}
```
