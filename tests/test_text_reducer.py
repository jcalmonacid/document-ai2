"""Pruebas del reductor de texto resolutivo."""
from app.utils.text_reducer import reducir_texto_resolutivo


def test_texto_corto_no_se_modifica():
    texto = 'RESOLUCIÓN DE ALCALDÍA N.° 1-2026. ARTÍCULO PRIMERO.- APROBAR algo.'
    assert reducir_texto_resolutivo(texto) == texto


def test_ancla_ignora_se_resuelve_falso_en_considerandos():
    """Si en los considerandos se cita 'se resuelve' (sin dos puntos) o se
    menciona otra norma, el ancla debe seguir cayendo en el RESUELVE: real."""
    encabezado = 'RESOLUCIÓN DE ALCALDÍA N.° 99-2026-MPH/A. Ayacucho. VISTO: ' + ('x' * 200)
    # Considerando con un 'se resuelve' falso (verbo, sin dos puntos) y mucho relleno
    considerando = (
        ' CONSIDERANDO: Que mediante otra resolución se resuelve aprobar un tema previo, '
        + ('relleno de considerandos y tablas presupuestales. ' * 600)
    )
    resolutivo = ' SE RESUELVE: ARTÍCULO PRIMERO.- AUTORIZAR_EL_OBJETIVO_REAL del documento. '
    tablas = ('fila de tabla presupuestal con montos. ' * 400)
    cierre = ' ARTÍCULO QUINTO.- NOTIFICAR. REGÍSTRESE, COMUNÍQUESE Y ARCHÍVESE.'
    texto = encabezado + considerando + resolutivo + tablas + cierre

    reducido = reducir_texto_resolutivo(texto, limite_chars=12000)

    # Debe conservar el objetivo real y el encabezado, y descartar parte de las tablas.
    assert 'AUTORIZAR_EL_OBJETIVO_REAL' in reducido
    assert '99-2026-MPH/A' in reducido
    assert len(reducido) < len(texto)


def test_respaldo_articulo_primero_sin_resuelve():
    encabezado = 'RESOLUCIÓN. ' + ('y' * 2000)
    cuerpo = ' ARTÍCULO PRIMERO.- DESIGNAR_RESPONSABLE. ' + ('dato. ' * 4000)
    texto = encabezado + cuerpo
    reducido = reducir_texto_resolutivo(texto, limite_chars=10000)
    assert 'DESIGNAR_RESPONSABLE' in reducido
