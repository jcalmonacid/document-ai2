import concurrent.futures
from app.services.pdf_service import procesar_archivo_pdf
from app.core.config import settings
from app.ui.state import ETAPA_RESULTADOS, actualizar_stats, avanzar_etapa
from app.utils.logger import logger
import streamlit as st

def renderizar_processing_section() -> None:
    if st.session_state.get('procesamiento_ejecutado', False):
        avanzar_etapa(st, ETAPA_RESULTADOS)
        st.rerun()
        return
    archivos = st.session_state.get('archivos_validados', [])
    if not archivos:
        st.warning('No hay archivos válidos para procesar.')
        avanzar_etapa(st, ETAPA_RESULTADOS)
        st.rerun()
        return
    st.subheader('⚡ Procesamiento Concurrente en curso')
    st.info(f'Procesando {len(archivos)} archivos ({settings.MAX_WORKERS} en paralelo).')
    progress_bar = st.progress(0)
    progress_text = st.empty()
    resultados = []
    errores = []
    total = len(archivos)
    log_container = st.container(height=350, border=True)

    def procesar_un_archivo(archivo):
        try:
            doc = procesar_archivo_pdf(archivo)
            return {'tipo': 'exito', 'archivo': archivo.name, 'doc': doc}
        except Exception as e:
            logger.error('Error procesando %s: %s', archivo.name, str(e), exc_info=True)
            return {'tipo': 'error', 'archivo': archivo.name, 'error': str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        futures = {executor.submit(procesar_un_archivo, arc): arc for arc in archivos}
        completados = 0
        for future in concurrent.futures.as_completed(futures):
            completados += 1
            res = future.result()
            progress_bar.progress(completados / total)
            progress_text.markdown(f'**Progreso ({completados}/{total}):** Último finalizado `{res['archivo']}`')
            with log_container:
                if res['tipo'] == 'exito':
                    resultados.append(res['doc'])
                    st.success(f'Finalizado: {res['archivo']}', icon='✅')
                else:
                    errores.append({'archivo': res['archivo'], 'error': res['error']})
                    st.error(f'Error en {res['archivo']}: {res['error']}', icon='❌')
    st.session_state['resultados_batch'] = resultados
    st.session_state['errores_procesamiento'] = errores
    st.session_state['procesamiento_ejecutado'] = True
    actualizar_stats(st, resultados, errores)
    avanzar_etapa(st, ETAPA_RESULTADOS)
    st.rerun()
