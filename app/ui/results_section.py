from datetime import datetime
import pandas as pd
import streamlit as st
from app.services.excel_service import generar_excel_consolidado

def _truncate(texto: str | None, limite: int=150) -> str:
    if not texto:
        return ''
    return texto if len(texto) <= limite else texto[:limite] + '...'

@st.cache_data(show_spinner=False)
def construir_dataframe_resultados(lista_docs: list) -> pd.DataFrame:
    filas = []
    for doc in lista_docs:
        filas.append({'Código': doc.codigo_generado, 'Tipo': doc.prefijo.upper(), 'Fecha': doc.fecha_archivo, 'Nombre Formal': doc.nombre_archivo_formal, 'Descripción': _truncate(getattr(doc, 'descripcion_excel', ''), 150), 'Fe de Erratas': doc.es_fe_de_erratas, 'Resumen IA': _truncate(getattr(doc.extraccion, 'resumen_ejecutivo', ''), 120), 'Archivo URL': doc.url_archivo or '', 'publication_type_id': doc.publication_type_id, 'category_id': doc.category_id})
    return pd.DataFrame(filas)

def renderizar_resultados_section(st) -> None:
    lista_docs = st.session_state.get('resultados_batch', [])
    errores = st.session_state.get('errores_procesamiento', [])
    col_titulo, col_boton = st.columns([0.6, 0.4])
    with col_titulo:
        st.subheader('📊 Resultados consolidados')
    with col_boton:
        if lista_docs:
            excel_file = generar_excel_consolidado(lista_docs)
            st.download_button(label='⬇️ Descargar Excel', data=excel_file, file_name=f'consolidado_normas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type='primary', width='stretch')
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Total Procesado', len(lista_docs) + len(errores))
    m2.metric('✅ Exitosos', len(lista_docs))
    m3.metric('❌ Errores', len(errores))
    m4.metric('📝 Fe de Erratas', sum((1 for d in lista_docs if d.es_fe_de_erratas)))
    if errores:
        with st.expander('⚠️ Ver detalle de errores', expanded=False):
            for item in errores:
                st.error(f'**{item['archivo']}**: {item['error']}')
    if not lista_docs:
        st.warning('No hay resultados exitosos para mostrar.')
        return
    st.divider()
    tab_tabla, tab_cards = st.tabs(['📋 Vista de Tabla', '📄 Detalle por Documento'])
    with tab_tabla:
        df = construir_dataframe_resultados(lista_docs)
        st.dataframe(df, width='stretch', hide_index=True, column_config={'Fecha': st.column_config.DateColumn('Fecha', format='DD/MM/YYYY'), 'Archivo URL': st.column_config.LinkColumn('Archivo URL', display_text='Abrir PDF'), 'Fe de Erratas': st.column_config.CheckboxColumn('Fe de Erratas'), 'publication_type_id': st.column_config.NumberColumn(format='%d'), 'category_id': st.column_config.NumberColumn(format='%d')})
    with tab_cards:
        for doc in lista_docs:
            with st.expander(f'📄 {doc.codigo_generado} — {doc.prefijo.upper()}', expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('**Datos del archivo físico**')
                    st.caption(f'Nombre físico: `{doc.nombre_archivo_fisico}`')
                    st.write(f'**Prefijo:** {doc.prefijo.upper()}')
                    st.write(f'**Número:** {doc.numero_correlativo}')
                    st.write(f'**Fecha:** {doc.fecha_archivo.strftime('%d/%m/%Y')}')
                    st.write(f'**Fe de Erratas:** {('Sí' if doc.es_fe_de_erratas else 'No')}')
                    if doc.url_archivo:
                        st.link_button('🌐 Ver PDF en Nube', doc.url_archivo, width='stretch')
                with col2:
                    st.markdown('**Extracción mediante IA**')
                    st.write(f'**Norma:** {getattr(doc.extraccion, 'nombre_norma_opcional', 'N/A')}')
                    st.write(f'**Resumen:** {getattr(doc.extraccion, 'resumen_ejecutivo', 'N/A')}')
                    st.markdown('**Contenido resolutivo:**')
                    st.info(getattr(doc.extraccion, 'contenido_resolutivo', 'No disponible'))
                st.caption(f'Metadatos internos ➔ publication_type_id: {doc.publication_type_id} | category_id: {doc.category_id}')
