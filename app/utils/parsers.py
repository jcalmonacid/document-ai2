from datetime import datetime, date
from typing import TypedDict

class ParserDict(TypedDict):
    prefijo: str
    numero_correlativo: int
    fecha_archivo: date
    es_fe_de_erratas: bool
    nombre_archivo_fisico: str

def parsear_metadata_filename(filename: str) -> ParserDict:
    clean_name = filename.lower().replace('.pdf', '').strip()
    es_fe_de_erratas = clean_name.endswith('_fe')
    if es_fe_de_erratas:
        clean_name = clean_name[:-3]
    partes = clean_name.split('_')
    if len(partes) < 3:
        raise ValueError(f"Formato de archivo inválido: '{filename}'. Se requiere: prefijo_numero_fecha.pdf (ej: rtran_282_18082025.pdf)")
    prefijo = partes[0]
    numero = partes[1]
    fecha_str = partes[2]
    try:
        fecha_obj = datetime.strptime(fecha_str, '%d%m%Y').date()
    except ValueError:
        raise ValueError(f"Fecha inválida en nombre de archivo: '{fecha_str}'. Use formato ddmmyyyy.")
    return {'prefijo': prefijo, 'numero_correlativo': int(numero), 'fecha_archivo': fecha_obj, 'es_fe_de_erratas': es_fe_de_erratas, 'nombre_archivo_fisico': filename}
