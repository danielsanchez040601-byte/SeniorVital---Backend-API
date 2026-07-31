# Usar imagen oficial de Python optimizada
FROM python:3.11-slim

# Variables de entorno para Python (evitar pyc y buffer)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configurar el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (por si pgvector u otras compilan)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando por defecto para arrancar la app
# Usamos ${PORT:-8000} para tomar el puerto dinámico de Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
