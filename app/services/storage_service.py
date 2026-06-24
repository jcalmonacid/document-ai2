import logging
from io import BytesIO
from datetime import datetime
from functools import lru_cache
from supabase import create_client, Client
from app.core.config import settings
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    return create_client(str(settings.SUPABASE_URL), settings.SUPABASE_KEY)

def subir_archivo_y_obtener_url(archivo: BytesIO, nombre_archivo: str, folder: str='resoluciones') -> str:
    cliente = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    archivo.seek(0)
    contenido = archivo.read()
    anio = datetime.now().year
    path_destino = f'{folder}/{anio}/{nombre_archivo}'
    try:
        logger.info(f'⬆️ Subiendo {nombre_archivo} a Supabase ({bucket}/{path_destino})...')
        res = cliente.storage.from_(bucket).upload(path=path_destino, file=contenido, file_options={'content-type': 'application/pdf', 'upsert': 'true'})
        public_url = cliente.storage.from_(bucket).get_public_url(path_destino)
        logger.info(f'✅ Subida exitosa. URL generada: {public_url}')
        archivo.seek(0)
        return public_url
    except Exception as e:
        logger.error(f'❌ Error CRÍTICO subiendo a Supabase: {str(e)}')
        if '404' in str(e) or 'not found' in str(e).lower():
            logger.error(f"🔍 El bucket '{bucket}' no fue encontrado. Verifique la configuración en Supabase y el .env")
        archivo.seek(0)
        return ''
