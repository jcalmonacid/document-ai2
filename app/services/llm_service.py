import logging
import re
import time
from typing import cast, Optional
from app.core.config import settings
from app.models.document import DatosExtraidosLLM
from app.prompts.extract_prompt import crear_prompt_extraccion_documentos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROVEEDOR = settings.AI_PROVIDER.lower().strip()


class ExtraccionIAError(Exception):
    """Se lanza cuando la extracción con IA falla o produce un resultado inválido.
    Permite que el documento se contabilice como ERROR (no como éxito silencioso)."""


# Palabras de la fórmula de cierre. Si el contenido resolutivo se reduce a esto,
# la extracción capturó el final del documento (texto truncado) y NO es válida.
_RE_SOLO_CIERRE = re.compile(
    r'REG[IÍ]STRESE|COMUN[IÍ]QUESE|C[UÚ]MPLASE|ARCH[IÍ]VESE|PUBL[IÍ]QUESE',
    re.IGNORECASE,
)


def _validar_resultado(resultado: DatosExtraidosLLM) -> DatosExtraidosLLM:
    """Verifica que la extracción sea utilizable. Lanza ExtraccionIAError si no."""
    contenido = (resultado.contenido_resolutivo or '').strip()
    if len(contenido) < 15:
        raise ExtraccionIAError('El contenido resolutivo extraído está vacío o es demasiado corto.')
    # Si al quitar las palabras de cierre no queda contenido sustantivo,
    # la IA capturó solo "REGÍSTRESE, COMUNÍQUESE, CÚMPLASE Y ARCHÍVESE".
    sin_cierre = _RE_SOLO_CIERRE.sub('', contenido).strip(' .,;:-y Y')
    if len(sin_cierre) < 15:
        raise ExtraccionIAError(
            'La extracción capturó solo la fórmula de cierre (REGÍSTRESE/COMUNÍQUESE...). '
            'Probable documento truncado o mal extraído; revise manualmente.'
        )
    return resultado


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
            keep_alive=-1,
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
            resultado = _validar_resultado(resultado)
            logger.info('✅ Extracción local exitosa.')
            return resultado
        except ExtraccionIAError as e:
            # Resultado inválido pero determinista (temperatura 0): reintentar no ayuda.
            logger.error(f'❌ Extracción inválida: {e}')
            raise
        except Exception as e:
            ultimo_error = e
            msg = str(e).lower()
            if 'not found' in msg or 'no such model' in msg or 'pull' in msg:
                logger.error(
                    f"❌ El modelo '{settings.OLLAMA_MODEL}' no está cargado en Ollama. "
                    f'Ejecute: docker compose exec ollama ollama pull {settings.OLLAMA_MODEL}'
                )
            else:
                logger.warning(f'⚠️ Error en Ollama (intento {intento}): {e}')
            if intento < max_intentos:
                time.sleep(2)
    raise ExtraccionIAError(
        f'Falló la extracción local tras {max_intentos} intentos. Último error: {ultimo_error}'
    )


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
            resultado = _validar_resultado(resultado)
            logger.info('✅ Extracción LLM exitosa.')
            return resultado
        except ExtraccionIAError as e:
            logger.error(f'❌ Extracción inválida: {e}')
            raise
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
            break
    raise ExtraccionIAError('TODAS LAS LLAVES DE RESPALDO SE HAN AGOTADO O FALLARON.')


# =====================================================================
# ENTRADA PÚBLICA
# =====================================================================
def extraer_datos_documento(texto_documento: str) -> DatosExtraidosLLM:
    if PROVEEDOR == 'gemini':
        return _extraer_con_gemini(texto_documento)
    return _extraer_con_ollama(texto_documento)
