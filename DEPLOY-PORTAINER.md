# 🚢 Despliegue en Portainer (paso a paso, desde cero)

Este proyecto se despliega como un **Stack** de Portainer. Incluye:

- `ollama` → motor de IA local (la API).
- `ollama-init` → descarga el modelo automáticamente la primera vez y termina (no es un error que aparezca como "exited").
- `document-ai-app` → la aplicación Streamlit. **Arranca solo cuando el modelo ya está descargado.**

Por eso, **el primer despliegue tarda varios minutos** (descarga del modelo, ~3–5 GB). Es normal.

---

## Requisitos de la VM

- Docker + Portainer ya instalados y funcionando.
- RAM libre según el modelo: `qwen2.5:7b-instruct` ≈ 8 GB · `qwen2.5:3b-instruct` ≈ 4 GB.
- ~10 GB de disco.
- Credenciales de Supabase (URL y KEY) a la mano.

---

## MÉTODO A — Stack desde repositorio Git (recomendado)

Portainer clona el repo (con el `Dockerfile`) y construye la imagen automáticamente.

1. En Portainer: **Stacks → + Add stack**.
2. **Name:** `document-ai`.
3. **Build method:** elige **Repository**.
4. **Repository URL:** la URL de tu repo, p. ej. `https://github.com/uticmunihuamanga-star/document-ai-pdf-prototype`.
5. **Repository reference:** `refs/heads/main`.
6. **Compose path:** `docker-compose.yml`.
7. Si el repo es **privado**: activa **Authentication** e ingresa tu **usuario de GitHub** y un **Personal Access Token**
   (GitHub → Settings → Developer settings → Personal access tokens → token con permiso `repo`).
8. Baja a **Environment variables → + Add an environment variable** y agrega:

   | Name | Value (ejemplo) |
   |---|---|
   | `SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `SUPABASE_KEY` | `tu-clave-anon-o-service-role` |
   | `SUPABASE_BUCKET` | `documentos` |
   | `OLLAMA_MODEL` | `qwen2.5:7b-instruct` *(o `qwen2.5:3b-instruct` si la VM es modesta)* |

9. Click en **Deploy the stack**. Espera (la primera vez descarga el modelo).
10. Abre la app en: **http://IP-DE-LA-VM:8501**

> Para verificar el avance: **Containers → ollama-init → Logs**. Cuando muestre
> `✅ Modelo descargado y listo` y el contenedor pase a *exited (0)*, la app quedará disponible.

---

## MÉTODO B — Editor web con imagen pre-construida (sin exponer el repo)

Si prefieres no dar acceso al repositorio, construye la imagen una vez en el host y luego pega el compose en Portainer.

**1) En el host (vía SSH), construir la imagen:**

```bash
# Copia/descomprime el proyecto en el host, por ejemplo en /opt/document-ai
cd /opt/document-ai
docker compose build        # crea la imagen 'document-ai-prototype:local'
```

**2) En Portainer:**

1. **Stacks → + Add stack → Name:** `document-ai`.
2. **Build method:** **Web editor**.
3. Pega el contenido del archivo **`docker-compose.portainer.yml`** (usa la imagen ya construida, no la construye).
4. Agrega las mismas **Environment variables** del Método A.
5. **Deploy the stack** → abre **http://IP-DE-LA-VM:8501**

---

## Cambiar de modelo después

1. Edita el stack → cambia la variable `OLLAMA_MODEL` (p. ej. a `gemma2:9b`).
2. **Update the stack**. El servicio `ollama-init` descargará el nuevo modelo automáticamente.

O manualmente, desde **Containers → ollama → Console** (`/bin/sh`):

```bash
ollama pull gemma2:9b
ollama list
```

---

## Usar Gemini (nube) en lugar de IA local

En las Environment variables del stack añade `AI_PROVIDER=gemini` y `GOOGLE_API_KEYS=clave1,clave2`, y vuelve a desplegar.
En ese modo no se usa Ollama.

---

## Solución de problemas

- **`ollama-init` aparece como "exited"** → es correcto: hizo su trabajo (descargar el modelo) y terminó.
- **La app no abre al principio** → espera a que termine la descarga del modelo (mira los logs de `ollama-init`).
- **Error "model not found" en la app** → el nombre en `OLLAMA_MODEL` no coincide con el descargado; corrígelo y actualiza el stack.
- **Muy lento por documento** → estás en CPU. Cambia a `qwen2.5:3b-instruct`, o sube `REQUEST_TIMEOUT` (p. ej. a 180).
- **GPU NVIDIA** → descomenta el bloque `deploy:` del servicio `ollama` en el compose.
