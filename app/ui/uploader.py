import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit.runtime.uploaded_file_manager import UploadedFile
from app.services.llm_service import extraer_datos_documento
from app.services.pdf_service import extraer_texto_pdf
from app.services.excel_service import generar_excel_consolidado
from app.models.document import DocumentoProcesado
from app.utils.logger import logger
from app.utils.parsers import parsear_metadata_filename
from app.services.storage_service import subir_archivo_y_obtener_url

def main():
    st.set_page_config(page_title='Inteligencia Documental - Batch', page_icon='📚', layout='wide', initial_sidebar_state='collapsed')
    if 'resultados_batch' not in st.session_state:
        st.session_state['resultados_batch'] = []
    st.title('📚 Procesamiento Masivo de Documentos')
    st.markdown('### Carga Múltiple y Consolidación Automática')
    st.divider()
    uploaded_files = st.file_uploader('Selecciona tus archivos PDF (formato: prefijo_numero_fecha.pdf)', type=['pdf'], accept_multiple_files=True, help='Arrastra y suelta todos los archivos aquí.')
    if uploaded_files:
        st.info(f'📂 {len(uploaded_files)} archivos seleccionados.')
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button('🚀 Iniciar Procesamiento', type='primary', width='stretch'):
                with st.spinner('Procesando documentos... esto puede tomar unos minutos.'):
                    procesar_batch(uploaded_files)
    if st.session_state['resultados_batch']:
        renderizar_resultados_consolidado()

def procesar_batch(files: list[UploadedFile]) -> None:
    lista_documentos_procesados = []
    total = len(files)
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_expander = st.expander('Ver detalles del procesamiento', expanded=True)
    for i, archivo_pdf in enumerate(files):
        nombre_archivo = archivo_pdf.name
        idx = i + 1
        status_text.text(f'⏳ ({idx}/{total}) Procesando: {nombre_archivo}...')
        progress_bar.progress(int(idx / total * 100))
        try:
            doc_procesado = procesar_un_archivo(archivo_pdf)
            lista_documentos_procesados.append(doc_procesado)
            log_expander.success(f'✅ {nombre_archivo} -> OK ({doc_procesado.codigo_generado})')
        except ValueError as ve:
            logger.warning(f'Validación fallida {nombre_archivo}: {ve}')
            log_expander.warning(f'⚠️ {nombre_archivo}: {str(ve)}')
        except Exception as e:
            logger.error(f'Error crítico {nombre_archivo}: {e}')
            log_expander.error(f'❌ {nombre_archivo}: {str(e)}')
    st.session_state['resultados_batch'] = lista_documentos_procesados
    status_text.success(f'🎉 Proceso finalizado. {len(lista_documentos_procesados)} documentos exitosos.')
    time.sleep(1)

def procesar_un_archivo(archivo_pdf: UploadedFile) -> DocumentoProcesado:
    metadata = parsear_metadata_filename(archivo_pdf.name)
    url_publica = subir_archivo_y_obtener_url(archivo=archivo_pdf, nombre_archivo=archivo_pdf.name)
    texto_extraido = extraer_texto_pdf(archivo_pdf)
    datos_ia = extraer_datos_documento(texto_extraido)
    doc_final = DocumentoProcesado(**metadata, extraccion=datos_ia, url_archivo=url_publica or 'Error al subir')
    return doc_final

def renderizar_resultados_consolidado():
    st.divider()
    st.subheader('📊 Vista Previa de Resultados')
    lista_docs = st.session_state['resultados_batch']
    if not lista_docs:
        st.warning('No se procesó ningún documento exitosamente.')
        return
    excel_file = generar_excel_consolidado(lista_docs)
    df_preview = pd.DataFrame([{'Código': d.codigo_generado, 'Fecha': d.fecha_archivo, 'Tipo': d.prefijo.upper(), 'Contenido (Extracto)': d.extraccion.contenido_resolutivo[:100] + '...'} for d in lista_docs])
    col1, col2 = st.columns([3, 1])
    with col1:
        st.dataframe(df_preview, width='stretch', hide_index=True)
    with col2:
        st.metric('Docs Procesados', len(lista_docs))
        st.download_button(label='⬇️ Descargar Excel', data=excel_file, file_name=f'consolidado_normas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type='primary')
