# 📄 Document AI - Prototipo de Procesamiento de PDFs (IA Local)

Este proyecto automatiza la extracción de metadatos, clasificación y generación de reportes de resoluciones municipales (PDF) utilizando IA y Pydantic.

> **🔒 Versión con IA LOCAL.** Por defecto el análisis se hace con **Ollama** dentro de la misma VM: el texto de los documentos **nunca sale del servidor**. Gemini (nube) queda como opción conmutable mediante la variable `AI_PROVIDER`.

## 🚀 Configuración Inicial

### 1. Preparar el entorno

```bash
git clone <url-del-repo>
cd document-ai-pdf-prototype
cp .env.example .env
```

> **Nota:** En modo local (`AI_PROVIDER=ollama`, por defecto) **no necesitas ninguna API Key**. Solo completa las credenciales de Supabase en `.env`. Las llaves de Google únicamente hacen falta si cambias a `AI_PROVIDER=gemini`.

### 2. Instalación de Dependencias

#### Opción A: Usando `uv` (Recomendado)

```bash
# Sincroniza el entorno y las dependencias automáticamente
uv sync
```

#### Opción B: Usando `pip` (Python estándar)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno:
# Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate

# Instalar dependencias
pip install -e .
```

### 3. Requisitos del Sistema (OCR)

Para procesar documentos escaneados localmente:

- **Tesseract OCR** (con datos de idioma español)
- **Poppler** (añadir a la ruta de variables de entorno)

---

## 🐳 Despliegue con IA Local en una VM (paso a paso)

El proyecto está dockerizado en dos servicios: la app (Streamlit) y **Ollama** (motor de IA local). Tesseract, Poppler y las librerías ya vienen dentro de las imágenes.

### Requisitos de la VM

- Docker Engine + plugin `docker compose` v2
- **RAM** según el modelo (ver tabla). El modelo por defecto (`qwen2.5:7b-instruct`) necesita ~8 GB de RAM libre.
- ~10 GB de disco (imágenes + modelo). GPU NVIDIA opcional.

### Elección del modelo según hardware

| Modelo (`OLLAMA_MODEL`) | RAM aprox. | Calidad/Español | Recomendado para |
|---|---|---|---|
| `qwen2.5:3b-instruct` | ~4 GB | Buena | VM modesta / solo CPU |
| `qwen2.5:7b-instruct` | ~8 GB | Muy buena | **Por defecto** |
| `llama3.1:8b-instruct-q4_0` | ~8 GB | Muy buena | Alternativa |
| `gemma2:9b` | ~10 GB | Excelente | VM con más recursos |

### Pasos

```bash
# 1. Clonar y entrar al proyecto
git clone <url-del-repo>
cd document-ai-pdf-prototype

# 2. Crear el archivo de entorno y editar credenciales de Supabase
cp .env.example .env
nano .env            # completa SUPABASE_URL y SUPABASE_KEY (deja AI_PROVIDER=ollama)

# 3. (Opcional) Elegir un modelo más ligero para esta VM
#    Edita OLLAMA_MODEL en .env, por ejemplo: OLLAMA_MODEL=qwen2.5:3b-instruct

# 4. Construir y levantar los servicios (app + Ollama + descarga del modelo)
#    La PRIMERA vez descarga el modelo automáticamente (~3-5 GB): tardará unos minutos.
docker compose up -d --build

# 5. (Opcional) Seguir el avance de la descarga del modelo
docker compose logs -f ollama-init     # mostrará "✅ Modelo descargado y listo"

# 6. Verificar que todo está arriba y sano
docker compose ps
docker compose exec ollama ollama list     # debe listar el modelo descargado

# 7. Abrir la aplicación
#    http://<IP-de-la-VM>:8501
```

> **Despliegue en Portainer:** consulta la guía **`DEPLOY-PORTAINER.md`** incluida en el proyecto.

### Comandos útiles

```bash
docker compose logs -f document-ai-app   # ver logs de la app
docker compose logs -f ollama            # ver logs del motor IA
docker compose restart document-ai-app   # reiniciar solo la app
docker compose down                      # detener (los modelos quedan en el volumen)
docker compose pull && docker compose up -d --build   # actualizar
```

> **Nota GPU:** si la VM tiene GPU NVIDIA con `nvidia-container-toolkit`, descomenta el bloque `deploy:` del servicio `ollama` en `docker-compose.yml` para acelerar la inferencia.

### Cambiar a Gemini (nube) si se necesita

En `.env`, pon `AI_PROVIDER=gemini` y añade `GOOGLE_API_KEYS=clave1,clave2`. Luego `docker compose up -d`. No hace falta tener Ollama corriendo en ese modo.

---

## 💻 Uso del Proyecto

### Ejecutar la Aplicación

```bash
# Con uv
uv run streamlit run main.py

# Con pip (con el entorno activo)
streamlit run main.py
```

### 📝 Convención de Nombres (Crítico)

Para la clasificación automática, los archivos deben seguir el formato:
`[prefijo]_[número]_[fecha].pdf` (Ej: `rtran_282_15122025.pdf`)

**Prefijos soportados:**

- `ralc`: Alcaldía
- `rtran`: Transporte
- `rgm`: Gerencia Municipal
- `rjefa`: Jefatura

---

## 🔄 Flujo General de Datos

```bash
Subida de PDF
      ↓
Extracción de metadatos del nombre
      ↓
Extracción de texto / OCR
      ↓
Análisis semántico con IA local (Ollama)
      ↓
Validación con Pydantic
      ↓
Almacenamiento en Supabase
      ↓
Generación de reporte Excel
```

## 🧪 Testing

```bash
# Con uv
uv run pytest

# Con pip
pytest
```

## 👥 Mantenimiento y Soporte

**Entidad responsable:**
Municipalidad Provincial de Huamanga (MP-HUAMANGA)
Unidad de Tecnologías de Información y Comunicaciones (UTIC)

**Contacto técnico:**
📧 [ledvirabp@gmail.com](mailto:ledvirabp@gmail.com)

**Última actualización:**
🔄 Junio de 2026
