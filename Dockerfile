# ==============================================================================
# Dockerfile Multietapa Optimizado para SeniorVital Backend en Render.com
# Estándar: ISO/IEC 25010 (Eficiencia y Portabilidad)
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para compilar paquetes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# --- Etapa Final de Ejecución Ligera ---
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    PORT=10000

# Instalar librerías de tiempo de ejecución
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde la etapa builder
COPY --from=builder /root/.local /root/.local

# Copiar código fuente de la aplicación
COPY . /app

# Puerto por defecto para Render.com (10000)
EXPOSE 10000

# Ejecutar el servidor ASGI con soporte para el puerto dinámico de Render ($PORT)
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
