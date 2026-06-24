import logging
import time
from typing import cast, Optional
from app.core.config import settings
from app.models.document import DatosExtraidosLLM
from app.prompts.extract_prompt import crear_prompt_extraccion_documentos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROVEEDOR = settings.AI_PROVIDER.lower().strip()

_RESULTADO_ERROR = DatosExtraidosLLM(
    nombre_norma_opcional=None,
    contenido_resolutivo='⚠️ ERROR: No se pudo extraer la información. Revise el motor de IA, el modelo cargado o el documento.',
    resumen_ejecutivo='No disponible.',
)


def _aplicar_salida_estructurada(modelo_base):
    """Adjunta el esquema Pydantic. Usa json_schema (más fiable en modelos locales)
    y cae a function_calling si la versión de la librería no lo soporta."""
    try:
        return modelo_base.with_structured_output(DatosExtraidosLLM, method='json_schema')
    except TypeError:
        return modelo_base.with_structured_output(DatosExtraidosLLM)


# =====================================================================
# PROVEEDOR: OLLAMA (IA LOCAL)
# =====================================================================
_cadena_ollama = None


def _get_cadena_ollama():
    global _cadena_ollama
    if _cadena_ollama is None:
        from langchain_ollama import ChatOllama
        modelo_base = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,
            num_ctx=settings.OLLAMA_NUM_CTX,
        )
        modelo_estructurado = _aplicar_salida_estructurada(modelo_base)
        _cadena_ollama = crear_prompt_extraccion_documentos() | modelo_estructurado
    return _cadena_ollama


def _extraer_con_ollama(texto_documento: str) -> DatosExtraidosLLM:
    max_intentos = max(1, settings.MAX_RETRIES)
    ultimo_error: Optional[Exception] = None
    for intento in range(1, max_intentos + 1):
        try:
            logger.info(
                f'🧠 Ollama [{settings.OLLAMA_MODEL}] intento {intento}/{max_intentos} '
                f'- Analizando {len(texto_documento)} chars...'
            )
            cadena = _get_cadena_ollama()
            resultado = cast(DatosExtraidosLLM, cadena.invoke({'text': texto_documento}))
            logger.info('✅ Extracción local exitosa.')
            return resultado
        except Exception as e:
            ultimo_error = e
            msg = str(e).lower()
            if 'not found' in msg or 'no such model' in msg or 'pull' in msg:
                logger.error(
                    f"❌ El modelo '{settings.OLLAMA_MODEL}' no está cargado en Ollama. "
                    f"Ejecute: docker compose exec ollama ollama pull {settings.OLLAMA_MODEL}"
                )
            else:
                logger.warning(f'⚠️ Error en Ollama (intento {intento}): {e}')
            if intento < max_intentos:
                time.sleep(2)
    logger.error(f'❌ Falló la extracción local tras {max_intentos} intentos. Último error: {ultimo_error}')
    return _RESULTADO_ERROR


# =====================================================================
# PROVEEDOR: GEMINI (IA EN LA NUBE, OPCIONAL) — con rotación de llaves
# =====================================================================
class GestorLlaves:

    def __init__(self, llaves: list[str]):
        if not llaves:
            raise ValueError('CRÍTICO: No hay GOOGLE_API_KEYS configuradas en el entorno.')
        self.llaves = llaves
        self.indice_actual = 0

    def obtener_llave_actual(self) -> str:
        return self.llaves[self.indice_actual]

    def rotar_llave(self) -> None:
        self.indice_actual = (self.indice_actual + 1) % len(self.llaves)


_gestor_llaves: Optional[GestorLlaves] = None
if PROVEEDOR == 'gemini':
    _gestor_llaves = GestorLlaves(settings.lista_llaves)


def _get_cadena_gemini(api_key: str):
    from langchain_google_genai import ChatGoogleGenerativeAI
    modelo_base = ChatGoogleGenerativeAI(
        model=settings.AI_MODEL,
        google_api_key=api_key,
        temperature=0.0,
        max_retries=1,
        request_timeout=settings.REQUEST_TIMEOUT,
    )
    modelo_estructurado = modelo_base.with_structured_output(DatosExtraidosLLM)
    return crear_prompt_extraccion_documentos() | modelo_estructurado


def _extraer_con_gemini(texto_documento: str) -> DatosExtraidosLLM:
    assert _gestor_llaves is not None
    intentos = 0
    max_intentos = len(_gestor_llaves.llaves)
    while intentos < max_intentos:
        llave_actual = _gestor_llaves.obtener_llave_actual()
        num_llave = _gestor_llaves.indice_actual + 1
        try:
            logger.info(f'🧠 Gemini (Llave {num_llave}/{max_intentos}) - Analizando {len(texto_documento)} chars...')
            cadena = _get_cadena_gemini(llave_actual)
            resultado = cast(DatosExtraidosLLM, cadena.invoke({'text': texto_documento}))
            logger.info('✅ Extracción LLM exitosa.')
            return resultado
        except Exception as e:
            intentos += 1
            error_msg = str(e).lower()
            if '429' in error_msg or 'resource_exhausted' in error_msg or 'quota' in error_msg:
                logger.warning(f'⚠️ Llave {num_llave} AGOTADA (Error 429). Rotando a la siguiente API Key...')
            else:
                logger.warning(f'⚠️ Error técnico en Llave {num_llave}: {str(e)}. Reintentando con siguiente llave...')
            _gestor_llaves.rotar_llave()
            if intentos < max_intentos:
                time.sleep(2)
                continue
            logger.error('❌ TODAS LAS LLAVES DE RESPALDO SE HAN AGOTADO O FALLARON.')
            break
    return _RESULTADO_ERROR


# =====================================================================
# ENTRADA PÚBLICA
# =====================================================================
def extraer_datos_documento(texto_documento: str) -> DatosExtraidosLLM:
    if PROVEEDOR == 'gemini':
        return _extraer_con_gemini(texto_documento)
    return _extraer_con_ollama(texto_documento)
