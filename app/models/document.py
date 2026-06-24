from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict
from pydantic import BaseModel, Field, computed_field, ConfigDict, field_validator
from .category_type import CategoryType
from .publication_type import PublicationType
ENTIDAD_SIGLA = 'MPH'
MAX_NORMA_LENGTH = 197

@dataclass(frozen=True)
class PrefixConfig:
    type: PublicationType = PublicationType.OTRO
    cat: CategoryType = CategoryType.GESTION_MUNICIPAL
    bb: str = ''
    name: str = 'RESOLUCIÓN GERENCIAL'

    def build_codigo(self, numero: int, anio: int, es_fe_de_erratas: bool=False) -> str:
        codigo = f'{numero}-{anio}-{ENTIDAD_SIGLA}'
        if self.bb:
            codigo = f'{codigo}/{self.bb}'
        if es_fe_de_erratas:
            codigo = f'{codigo}-FE'
        return codigo
PREFIX_MAPPING: Dict[str, PrefixConfig] = {'ralc': PrefixConfig(type=PublicationType.RESOLUCION_ALCALDIA, cat=CategoryType.GESTION_PUBLICA, bb='A', name='RESOLUCIÓN DE ALCALDÍA'), 'acuer': PrefixConfig(type=PublicationType.ACUERDO_CONCEJO, cat=CategoryType.GESTION_MUNICIPAL, bb='CM', name='ACUERDO DE CONCEJO'), 'decre': PrefixConfig(type=PublicationType.DECRETO_ALCALDIA, cat=CategoryType.GESTION_MUNICIPAL, bb='A', name='DECRETO DE ALCALDÍA'), 'rgm': PrefixConfig(type=PublicationType.RESOLUCION_GERENCIA_MUNICIPAL, cat=CategoryType.GESTION_MUNICIPAL, bb='GM', name='RESOLUCIÓN GERENCIA MUNICIPAL'), 'ordmu': PrefixConfig(type=PublicationType.ORDENANZA_MUNICIPAL, cat=CategoryType.GESTION_MUNICIPAL, bb='CM', name='ORDENANZA MUNICIPAL'), 'actasesion': PrefixConfig(type=PublicationType.ACTA_SESION, cat=CategoryType.GESTION_MUNICIPAL, bb='CM', name='ACTA DE SESIÓN'), 'conv': PrefixConfig(type=PublicationType.CONVENIO, cat=CategoryType.GESTION_MUNICIPAL, bb='', name='CONVENIO'), 'dir': PrefixConfig(type=PublicationType.DIRECTIVA, cat=CategoryType.GESTION_MUNICIPAL, bb='', name='DIRECTIVA'), 'rsgdt': PrefixConfig(type=PublicationType.RESOLUCION_GERENCIA_DESARROLLO_TERRITORIAL, cat=CategoryType.GESTION_MUNICIPAL, bb='GDT', name='RESOLUCIÓN GERENCIAL'), 'regl': PrefixConfig(type=PublicationType.REGLAMENTO, cat=CategoryType.GESTION_MUNICIPAL, bb='', name='REGLAMENTO'), 'craet': PrefixConfig(type=PublicationType.RESOLUCION_CRAET, cat=CategoryType.GESTION_MUNICIPAL, bb='CRAET', name='RESOLUCIÓN DE CRAET'), 'rtran': PrefixConfig(type=PublicationType.RESOLUCION_GERENCIA_TRANSPORTES, cat=CategoryType.GESTION_MUNICIPAL, bb='GT', name='RESOLUCIÓN DE GERENCIA'), 'rjefa': PrefixConfig(type=PublicationType.RESOLUCION_JEFATURAL, cat=CategoryType.GESTION_MUNICIPAL, bb='OAF-U-RRHH', name='RESOLUCIÓN JEFATURAL'), 'rda': PrefixConfig(type=PublicationType.RESOLUCION_DIRECTORAL_ADMINISTRACION, cat=CategoryType.GESTION_MUNICIPAL, bb='OAF', name='RESOLUCIÓN DIRECTORAL'), 'rseci': PrefixConfig(type=PublicationType.RESOLUCION_GERENCIA_SEGURIDAD_CIUDADANA, cat=CategoryType.GESTION_MUNICIPAL, bb='46', name='RESOLUCIÓN GERENCIAL'), 'rdeco': PrefixConfig(type=PublicationType.RESOLUCION_GERENCIA_DESARROLLO_ECONOMICO, cat=CategoryType.ECONOMIA_Y_FINANZAS, bb='42', name='RESOLUCIÓN GERENCIAL DE DESARROLLO ECONÓMICO')}

class DatosExtraidosLLM(BaseModel):
    nombre_norma_opcional: Optional[str] = Field(None, description="Título del tema o asunto ESPECÍFICO si aparece explícitamente antes del cuerpo. Ejemplo: 'APRUEBAN REGLAMENTO DE...'. Si no hay un título claro, devolver null.")
    contenido_resolutivo: str = Field(..., description="Extracción LITERAL y COMPLETA del primer párrafo resolutivo o 'Artículo Primero'. INSTRUCCIONES CRÍTICAS: 1. NO RESUMAS. Copia el texto exacto. 2. Elimina la etiqueta inicial (ej: borra 'ARTÍCULO PRIMERO.-'). 3. Incluye todo el texto hasta antes del 'ARTÍCULO SEGUNDO'. 4. Corrige saltos de línea innecesarios para que sea un solo párrafo fluido.5. Este campo es el MÁS IMPORTANTE para la columna 'Descripción' en Excel, así que hazlo lo mejor posible.6. Si el documento tiene un formato muy irregular, haz tu mejor esfuerzo por extraer el contenido resolutivo, pero no inventes ni adivines nada que no esté claro en el texto.7. Corrige palabras rotas o errores de OCR en este fragmento. El objetivo es que el texto sea legible y coherente, incluso si el PDF original tiene problemas de formato.")
    resumen_ejecutivo: Optional[str] = Field(None, description='Resumen muy breve (1-2 líneas) de lo que trata la resolución para referencia rápida. Que sea claro y conciso.')

class DocumentoProcesado(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nombre_archivo_fisico: str
    prefijo: str
    numero_correlativo: int
    fecha_archivo: date
    es_fe_de_erratas: bool = False
    url_archivo: Optional[str] = None
    extraccion: DatosExtraidosLLM

    @field_validator('prefijo')
    @classmethod
    def validar_prefijo(cls, v: str) -> str:
        if v.lower() not in PREFIX_MAPPING:
            raise ValueError(f'Prefijo desconocido: {v}')
        return v.lower()

    def _config(self) -> PrefixConfig:
        return PREFIX_MAPPING.get(self.prefijo, PrefixConfig())

    @computed_field
    def publication_type_id(self) -> int:
        return self._config().type.value

    @computed_field
    def category_id(self) -> int:
        return self._config().cat.value

    @computed_field
    def codigo_generado(self) -> str:
        return self._config().build_codigo(numero=self.numero_correlativo, anio=self.fecha_archivo.year, es_fe_de_erratas=self.es_fe_de_erratas)

    @computed_field
    def titulo_excel(self) -> str:
        return f'{self.codigo_generado}.'

    @computed_field
    def nombre_norma_excel(self) -> str:
        base = self.extraccion.contenido_resolutivo or self.extraccion.nombre_norma_opcional
        if not base:
            return 'N/A'
        base = base[:MAX_NORMA_LENGTH] + '...' if len(base) > MAX_NORMA_LENGTH else base
        return f'FE DE ERRATAS: {base}' if self.es_fe_de_erratas else base

    @computed_field
    def descripcion_excel(self) -> str:
        texto = self.extraccion.contenido_resolutivo
        if self.es_fe_de_erratas:
            return f'FE DE ERRATAS: {texto}'
        return texto

    @computed_field
    def nombre_archivo_formal(self) -> str:
        resolution_base_name = f'{self._config().name} N.° {self.codigo_generado}'
        if self.es_fe_de_erratas:
            return f'FE DE ERRATAS DE LA {resolution_base_name}'
        return resolution_base_name

    @computed_field
    def descripcion_documento_excel(self) -> str:
        return f'Archivo PDF de la {self.nombre_archivo_formal}'
