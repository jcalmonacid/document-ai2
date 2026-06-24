from collections import Counter
from typing import Any
from app.models.document import DocumentoProcesado
ETAPA_CARGA = 'carga'
ETAPA_PROCESAMIENTO = 'procesamiento'
ETAPA_RESULTADOS = 'resultados'

def _get_default_stats() -> dict:
    return {'total': 0, 'exitosos': 0, 'errores': 0, 'fe_erratas': 0, 'por_prefijo': {}}

def inicializar_estado(st: Any) -> None:
    if 'etapa_actual' not in st.session_state:
        st.session_state['etapa_actual'] = ETAPA_CARGA
    if 'archivos_subidos' not in st.session_state:
        st.session_state['archivos_subidos'] = []
    if 'archivos_validados' not in st.session_state:
        st.session_state['archivos_validados'] = []
    if 'archivos_rechazados' not in st.session_state:
        st.session_state['archivos_rechazados'] = []
    if 'resultados_batch' not in st.session_state:
        st.session_state['resultados_batch'] = []
    if 'errores_procesamiento' not in st.session_state:
        st.session_state['errores_procesamiento'] = []
    if 'stats' not in st.session_state:
        st.session_state['stats'] = _get_default_stats()
    if 'procesamiento_ejecutado' not in st.session_state:
        st.session_state['procesamiento_ejecutado'] = False

def avanzar_etapa(st: Any, etapa: str) -> None:
    st.session_state['etapa_actual'] = etapa

def resetear_estado(st: Any) -> None:
    st.session_state['etapa_actual'] = ETAPA_CARGA
    st.session_state['archivos_subidos'] = []
    st.session_state['archivos_validados'] = []
    st.session_state['archivos_rechazados'] = []
    st.session_state['resultados_batch'] = []
    st.session_state['errores_procesamiento'] = []
    st.session_state['procesamiento_ejecutado'] = False
    st.session_state['stats'] = _get_default_stats()

def actualizar_stats(st: Any, documentos: list[DocumentoProcesado], errores: list[dict]) -> None:
    conteo_prefijos = Counter((doc.prefijo.upper() for doc in documentos))
    st.session_state['stats'] = {'total': len(documentos) + len(errores), 'exitosos': len(documentos), 'errores': len(errores), 'fe_erratas': sum((1 for doc in documentos if doc.es_fe_de_erratas)), 'por_prefijo': dict(conteo_prefijos)}
