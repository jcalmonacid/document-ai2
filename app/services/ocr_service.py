import logging
import sys
import shutil
import os
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
import PyPDF2
from app.core.config import settings
logger = logging.getLogger(__name__)
if sys.platform.startswith('win'):
    if settings.TESSERACT_PATH and settings.TESSERACT_PATH.exists():
        pytesseract.pytesseract.tesseract_cmd = str(settings.TESSERACT_PATH)
    else:
        logger.warning('⚠️ Ruta de Tesseract no configurada en Windows. El OCR podría fallar.')

def detectar_pdf_escaneado(archivo_pdf: BytesIO) -> bool:
    try:
        archivo_pdf.seek(0)
        pdf_reader = PyPDF2.PdfReader(archivo_pdf)
        num_paginas = len(pdf_reader.pages)
        if num_paginas == 0:
            return False
        texto_total = ''
        for i in range(min(3, num_paginas)):
            texto = pdf_reader.pages[i].extract_text() or ''
            texto_total += texto
        if num_paginas > 0:
            promedio_caracteres = len(texto_total.strip()) / min(3, num_paginas)
        else:
            promedio_caracteres = 0
        es_escaneado = promedio_caracteres < 50
        logger.info(f'🔍 Diagnóstico PDF: {promedio_caracteres:.1f} chars/pág. ¿Es escaneado?: {('SÍ' if es_escaneado else 'NO')}')
        archivo_pdf.seek(0)
        return es_escaneado
    except Exception as e:
        logger.warning(f'Error detectando tipo PDF: {e}')
        archivo_pdf.seek(0)
        return True

def obtener_ruta_poppler_optimizada():
    if not sys.platform.startswith('win'):
        return None
    if settings.POPPLER_PATH and settings.POPPLER_PATH.exists():
        return str(settings.POPPLER_PATH)
    ruta_ejecutable = shutil.which('pdfinfo')
    if ruta_ejecutable:
        return os.path.dirname(ruta_ejecutable)
    logger.error('❌ POPPLER NO ENCONTRADO EN WINDOWS. El OCR fallará.')
    return None

def extraer_texto_con_ocr(archivo_pdf: BytesIO, idioma: str='spa') -> str:
    try:
        archivo_pdf.seek(0)
        logger.info('⏳ Iniciando proceso de OCR...')
        ruta_poppler = obtener_ruta_poppler_optimizada()
        if sys.platform.startswith('win') and (not ruta_poppler):
            raise RuntimeError('No se encontró Poppler en Windows. Configura POPPLER_PATH en .env')
        convert_kwargs = {'dpi': 200, 'fmt': 'jpeg', 'thread_count': 2}
        if ruta_poppler:
            convert_kwargs['poppler_path'] = ruta_poppler
        imagenes = convert_from_bytes(archivo_pdf.read(), **convert_kwargs)
        texto_completo = []
        total = len(imagenes)
        for i, imagen in enumerate(imagenes):
            logger.debug(f'📸 OCR Procesando página {i + 1}/{total}')
            try:
                texto_pagina = pytesseract.image_to_string(imagen, lang=idioma, config='--psm 3')
                if texto_pagina.strip():
                    texto_completo.append(f'--- Página {i + 1} (OCR) ---')
                    texto_completo.append(texto_pagina.strip())
            except Exception as e:
                logger.error(f'Fallo OCR en página {i + 1}: {e}')
        resultado = '\n\n'.join(texto_completo)
        archivo_pdf.seek(0)
        return resultado
    except Exception as e:
        logger.error(f'🔥 Fallo crítico en motor OCR: {e}')
        archivo_pdf.seek(0)
        raise RuntimeError(f'Error en motor OCR: {str(e)}')

def extraer_texto_hibrido(archivo_pdf: BytesIO) -> tuple[str, str]:
    try:
        es_escaneado = detectar_pdf_escaneado(archivo_pdf)
        if not es_escaneado:
            try:
                archivo_pdf.seek(0)
                pdf_reader = PyPDF2.PdfReader(archivo_pdf)
                texto_list = []
                for page in pdf_reader.pages:
                    texto_list.append(page.extract_text() or '')
                texto_final = '\n'.join(texto_list)
                if len(texto_final.strip()) > 50:
                    logger.info('✅ Extracción nativa exitosa.')
                    archivo_pdf.seek(0)
                    return (texto_final, 'nativo')
            except Exception as e:
                logger.warning(f'Fallo extracción nativa, intentando OCR: {e}')
        logger.info('⚠️ Documento escaneado o ilegible. Activando OCR.')
        texto_ocr = extraer_texto_con_ocr(archivo_pdf)
        return (texto_ocr, 'ocr')
    except Exception as e:
        logger.error(f'Error en extracción híbrida: {e}')
        raise e
