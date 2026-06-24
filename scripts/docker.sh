#!/bin/bash

# ==============================================
# Comandos Docker para Document AI PDF Prototype
# ==============================================

# 1. CONSTRUCCIÓN DE LA IMAGEN
echo "🔨 Construir imagen Docker..."
docker-compose build

# 2. EJECUTAR LA APLICACIÓN
echo "🚀 Iniciar aplicación..."
docker-compose up -d

# 3. VER LOGS EN TIEMPO REAL
echo "📋 Ver logs..."
docker-compose logs -f

# 4. DETENER LA APLICACIÓN
echo "🛑 Detener aplicación..."
docker-compose down

# 5. RECONSTRUIR COMPLETAMENTE (limpia cache)
echo "♻️ Reconstruir desde cero..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 6. ACCEDER A LA SHELL DEL CONTENEDOR (debugging)
echo "🐚 Acceder al contenedor..."
docker-compose exec document-ai-app /bin/bash

# 7. VER ESTADO DE SALUD
echo "🏥 Ver estado de salud..."
docker-compose ps