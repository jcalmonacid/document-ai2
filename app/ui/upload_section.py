import pandas as pd
import streamlit as st
from app.models.document import PREFIX_MAPPING
from app.ui.state import ETAPA_PROCESAMIENTO, avanzar_etapa
from app.utils.parsers import parsear_metadata_filename

@st.cache_data(show_spinner=False)
def _tabla_prefijos() -> pd.DataFrame:
    filas = []
    for prefijo, config in PREFIX_MAPPING.items():
        filas.append({'Prefijo': prefijo.upper(), 'Tipo': config.name, 'ID Tipo': config.type.value, 'Código BB': config.bb or '—'})
    return pd.DataFrame(filas)

def _validar_archivos(uploaded_files: list) -> tuple[list, list[dict], pd.DataFrame]:
    validos = []
    rechazados = []
    preview = []
    for archivo in uploaded_files:
        try:
            metadata = parsear_metadata_filename(archivo.name)
            validos.append(archivo)
            preview.append({'Archivo': archivo.name, 'Prefijo': (metadata['prefijo'] or 'DESCONOCIDO').upper(), 'Número': metadata['numero_correlativo'], 'Fecha': metadata['fecha_archivo'], 'Estado': '✅ Válido'})
        except Exception as e:
            rechazados.append({'archivo': archivo.name, 'error': str(e)})
            preview.append({'Archivo': archivo.name, 'Prefijo': '—', 'Número': '—', 'Fecha': '—', 'Estado': '❌ Inválido'})
    return (validos, rechazados, pd.DataFrame(preview))

def renderizar_upload_section(st) -> None:
    st.subheader('📁 Carga y validación')
    st.markdown('Sube tus PDFs con el formato oficial: `prefijo_numero_ddmmyyyy.pdf`.')
    uploaded_files = st.file_uploader('Selecciona archivos PDF', type=['pdf'], accept_multiple_files=True, help='Arrastra y suelta múltiples archivos para procesamiento masivo.')
    if not uploaded_files:
        st.info('💡 Sube uno o más documentos para iniciar. Aquí tienes los prefijos válidos:')
        st.dataframe(_tabla_prefijos(), width='stretch', hide_index=True)
        return
    validos, rechazados, df_preview = _validar_archivos(uploaded_files)
    st.session_state['archivos_subidos'] = uploaded_files
    st.session_state['archivos_validados'] = validos
    st.session_state['archivos_rechazados'] = rechazados
    st.write('### 📊 Resumen de validación')
    col1, col2, col3 = st.columns(3)
    col1.metric('Total Seleccionados', len(uploaded_files))
    col2.metric('✅ Válidos', len(validos))
    col3.metric('❌ Inválidos', len(rechazados), delta_color='inverse')
    st.dataframe(df_preview, width='stretch', hide_index=True)
    if rechazados:
        with st.expander('⚠️ Ver motivo de rechazo', expanded=False):
            for item in rechazados:
                st.error(f'**{item['archivo']}**: {item['error']}')
    st.divider()
    if st.button('🚀 Iniciar procesamiento de PDFs', type='primary', width='stretch', key='btn_iniciar_procesamiento', disabled=len(validos) == 0):
        st.session_state['procesamiento_ejecutado'] = False
        avanzar_etapa(st, ETAPA_PROCESAMIENTO)
        st.rerun()
