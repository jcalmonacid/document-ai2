import PyPDF2
import logging
from io import BytesIO
from typing import Callable, Optional
from app.models.document import DocumentoProcesado
from app.services.llm_service import extraer_datos_documento
from app.services.ocr_service import extraer_texto_hibrido
from app.services.storage_service import subir_archivo_y_obtener_url
from app.utils.parsers import parsear_metadata_filename
logger = logging.getLogger(__name__)

def extraer_texto_pdf(archivo_pdf: BytesIO) -> str:
    try:
        archivo_pdf.seek(0)
        texto_extraido, metodo = extraer_texto_hibrido(archivo_pdf)
        if not texto_extraido or not texto_extraido.strip():
            raise ValueError('El PDF no contiene texto digital extraíble (posible imagen corrupta o en blanco).')
        logger.info(f"Texto extraído exitosamente usando método '{metodo}': {len(texto_extraido)} caracteres")
        archivo_pdf.seek(0)
        return texto_extraido
    except Exception as e:
        logger.error(f'Fallo en lectura de PDF: {str(e)}', exc_info=True)
        raise RuntimeError(f'Fallo en lectura de PDF: {str(e)}')

def obtener_numero_paginas(archivo_pdf: BytesIO) -> int:
    try:
        archivo_pdf.seek(0)
        pdf_reader = PyPDF2.PdfReader(archivo_pdf)
        num_paginas = len(pdf_reader.pages)
        archivo_pdf.seek(0)
        return num_paginas
    except Exception as e:
        logger.warning(f'Error al contar páginas: {str(e)}')
        archivo_pdf.seek(0)
        return 0

def procesar_archivo_pdf(archivo_pdf: BytesIO, on_step: Optional[Callable[[str], None]]=None) -> DocumentoProcesado:

    def reportar(paso: str) -> None:
        if on_step:
            on_step(paso)
    reportar('📛 Validando nombre de archivo...')
    metadata = parsear_metadata_filename(archivo_pdf.name)
    reportar('☁️ Subiendo archivo a almacenamiento...')
    url_publica = subir_archivo_y_obtener_url(archivo=archivo_pdf, nombre_archivo=archivo_pdf.name)
    reportar('📖 Extrayendo texto del PDF...')
    texto_extraido = extraer_texto_pdf(archivo_pdf)
    reportar('🧠 Analizando contenido con IA...')
    datos_ia = extraer_datos_documento(texto_extraido)
    reportar('✅ Consolidando resultado final...')
    return DocumentoProcesado(**metadata, extraccion=datos_ia, url_archivo=url_publica or 'Error al subir')
