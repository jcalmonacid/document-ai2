"""Reduce el texto de resoluciones muy largas para que la parte resolutiva
(ARTÍCULO PRIMERO) siempre entre en la ventana de contexto del modelo.

Estrategia: cuando el documento supera el límite, se conserva el ENCABEZADO
(tipo, número, fecha, VISTO), la PARTE RESOLUTIVA (anclada en el último
"RESUELVE:" para evitar falsos positivos de los considerandos) y el CIERRE
(artículos finales). Se descarta el bloque intermedio de tablas/anexos, que
es el ruido que desbordaba el contexto.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Tamaños (en caracteres) de las partes que SIEMPRE se conservan.
TAM_ENCABEZADO = 1500
TAM_CIERRE = 2500

# Ancla principal: "RESUELVE:" / "SE RESUELVE:" / "DECRETA:" / "ACUERDA:" como
# encabezado de sección. Exigimos los DOS PUNTOS para descartar el verbo
# "se resuelve" usado dentro de una oración en los considerandos.
_RE_RESUELVE = re.compile(r'(?:SE\s+)?(?:RESUELVE|DECRETA|ACUERDA)\s*:', re.IGNORECASE)

# Respaldo: "ARTÍCULO PRIMERO" / "ARTÍCULO 1°".
_RE_ART_PRIMERO = re.compile(r'ART[IÍ]CULO\s+(?:PRIMERO|1\s*[°º]?)', re.IGNORECASE)

_MARCA_OMISION = '\n[... contenido intermedio omitido (tablas/anexos) ...]\n'


def reducir_texto_resolutivo(texto: str, limite_chars: int = 18000) -> str:
    """Devuelve el texto tal cual si cabe; si no, una versión reducida que
    garantiza incluir la parte resolutiva."""
    if not texto:
        return texto
    if len(texto) <= limite_chars:
        return texto

    encabezado = texto[:TAM_ENCABEZADO]

    # Inicio de la parte resolutiva: ÚLTIMA coincidencia de "RESUELVE:".
    # La parte operativa va siempre DESPUÉS de todos los considerandos, por lo
    # que cualquier "resuelve" citado antes queda correctamente descartado.
    matches = list(_RE_RESUELVE.finditer(texto))
    if matches:
        inicio_op = matches[-1].start()
        ancla = 'RESUELVE:'
    else:
        m = list(_RE_ART_PRIMERO.finditer(texto))
        inicio_op = m[-1].start() if m else TAM_ENCABEZADO
        ancla = 'ARTÍCULO PRIMERO' if m else 'inicio'

    presupuesto_operativa = limite_chars - TAM_CIERRE

    # Caso: la parte resolutiva está muy arriba (ya dentro del encabezado).
    if inicio_op <= TAM_ENCABEZADO:
        cuerpo = texto[:presupuesto_operativa]
        cierre = texto[-TAM_CIERRE:]
        reducido = cuerpo + _MARCA_OMISION + cierre
    else:
        espacio_operativa = presupuesto_operativa - TAM_ENCABEZADO
        operativa = texto[inicio_op: inicio_op + espacio_operativa]
        cierre = texto[-TAM_CIERRE:]
        reducido = encabezado + _MARCA_OMISION + operativa + '\n[...]\n' + cierre

    logger.info(
        f'📄 Texto largo reducido: {len(texto):,} → {len(reducido):,} caracteres '
        f'(ancla resolutiva: {ancla} en pos {inicio_op:,}).'
    )
    return reducido
