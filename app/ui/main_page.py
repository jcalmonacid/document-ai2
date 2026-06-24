import streamlit as st
from app.ui.processing_section import renderizar_processing_section
from app.ui.results_section import renderizar_resultados_section
from app.ui.sidebar import renderizar_sidebar
from app.ui.state import ETAPA_CARGA, ETAPA_PROCESAMIENTO, ETAPA_RESULTADOS, inicializar_estado
from app.ui.upload_section import renderizar_upload_section

def main() -> None:
    st.set_page_config(page_title='Inteligencia Documental - Batch', page_icon='📚', layout='wide', initial_sidebar_state='expanded')
    inicializar_estado(st)
    renderizar_sidebar(st)
    st.title('📚 Plataforma de Control Documental')
    st.markdown('### Plataforma institucional de clasificación y extracción inteligente')
    st.divider()
    etapa = st.session_state.get('etapa_actual', ETAPA_CARGA)
    if etapa == ETAPA_CARGA:
        renderizar_upload_section(st)
    elif etapa == ETAPA_PROCESAMIENTO:
        renderizar_processing_section()
    elif etapa == ETAPA_RESULTADOS:
        renderizar_resultados_section(st)
    else:
        renderizar_upload_section(st)
