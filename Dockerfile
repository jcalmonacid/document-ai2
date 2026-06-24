# syntax=docker/dockerfile:1

# ==========================================
# ETAPA 1: Builder (Compilación de dependencias)
# ==========================================
FROM python:3.12-slim AS builder

# Instalar uv directamente desde su imagen oficial (Método recomendado y más rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Configurar uv para contenedores
# UV_COMPILE_BYTECODE=1: Compila a .pyc para que la app arranque más rápido
# UV_LINK_MODE=copy: Copia archivos en lugar de usar hardlinks (más seguro entre etapas Docker)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Copiamos SOLO los archivos de definición de dependencias primero
# Esto permite que Docker use la caché si no has cambiado dependencias
COPY pyproject.toml uv.lock ./

# Instalamos las dependencias
# --frozen: Falla si el uv.lock no coincide con pyproject.toml (seguridad)
# --no-dev: No instala herramientas de desarrollo
# --no-install-project: Solo instala las librerías, no tu código (tu código se copia en la etapa final)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ==========================================
# ETAPA 2: Runner (Imagen final ligera)
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para OCR y PDF
# Incluye 'tesseract-ocr-spa' para español
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios
RUN groupadd -r appuser && useradd -m -r -g appuser appuser

# Copiar el entorno virtual (.venv) creado en la etapa builder
# Esto contiene todas tus librerías de Python ya instaladas
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copiar el código fuente de tu aplicación
COPY --chown=appuser:appuser . .

# Configurar variables de entorno
# PATH: Añadimos el .venv al inicio para que 'python' y 'streamlit' funcionen directo
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Configuración servidor Streamlit
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Cambiar al usuario seguro
USER appuser

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

# Ejecutar la aplicación
CMD ["streamlit", "run", "main.py"]