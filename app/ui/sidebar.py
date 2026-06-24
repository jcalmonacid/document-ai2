from app.core.config import settings
from app.ui.state import resetear_estado

def renderizar_sidebar(st) -> None:
    st.sidebar.title('🏛️ MPH - UTIC')
    st.sidebar.caption('Municipalidad Provincial de Huamanga')
    st.sidebar.caption('Sistema de Procesamiento Documental IA')
    st.sidebar.write('')
    if st.sidebar.button('🗑️ Nueva Sesión', width='stretch', key='sidebar_btn_nueva_sesion', type='primary'):
        resetear_estado(st)
        st.rerun()
    st.sidebar.divider()

    proveedor = settings.AI_PROVIDER.lower().strip()
    with st.sidebar.expander('⚙️ Configuración', expanded=False):
        if proveedor == 'ollama':
            st.write('**Motor IA:** 🖥️ Local (Ollama)')
            st.write(f'**Modelo:** `{settings.OLLAMA_MODEL}`')
            st.caption('🔒 Procesamiento 100% en servidor propio')
        else:
            total_llaves = len(settings.lista_llaves)
            estado_api = f'✅ {total_llaves} Llave(s)' if total_llaves > 0 else '❌ Error'
            st.write('**Motor IA:** ☁️ Nube (Gemini)')
            st.write(f'**API Google:** {estado_api}')
            st.write(f'**Modelo:** `{settings.AI_MODEL}`')
            if total_llaves > 1:
                st.caption('🔄 Rotación activa')

    stats = st.session_state.get('stats', {})
    st.sidebar.subheader('📊 Resumen')
    c1, c2 = st.sidebar.columns(2)
    c1.metric('Total', stats.get('total', 0))
    c2.metric('Éxitos', stats.get('exitosos', 0))
    c3, c4 = st.sidebar.columns(2)
    errores = stats.get('errores', 0)
    c3.metric('Errores', errores, delta_color='inverse')
    c4.metric('FEs', stats.get('fe_erratas', 0))
    por_prefijo = stats.get('por_prefijo', {})
    if por_prefijo:
        with st.sidebar.expander('📋 Detalle por Tipo', expanded=False):
            st.dataframe([{'Tipo': k.upper(), 'Cant.': v} for k, v in por_prefijo.items()], width='stretch', hide_index=True)
    st.sidebar.write('')
    st.sidebar.write('')
    st.sidebar.divider()
    st.sidebar.caption('👨\u200d💻 Desarrollado por **ledvir**')
    st.sidebar.caption('© 2026 UTIC - MPH')
