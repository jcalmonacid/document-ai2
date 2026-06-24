from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator, model_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys

class Settings(BaseSettings):
    # --- Proveedor de IA ---
    # 'ollama' = IA local (por defecto, sin salida a internet)
    # 'gemini' = IA en la nube de Google (requiere GOOGLE_API_KEYS)
    AI_PROVIDER: str = Field(default='ollama', min_length=1)

    # --- Configuración Ollama (IA local) ---
    OLLAMA_BASE_URL: str = Field(default='http://ollama:11434', min_length=1)
    OLLAMA_MODEL: str = Field(default='qwen2.5:7b-instruct', min_length=1)
    OLLAMA_NUM_CTX: int = Field(default=8192, ge=2048)

    # --- Configuración Gemini (IA en la nube, opcional) ---
    GOOGLE_API_KEYS: str = Field(default='')
    AI_MODEL: str = Field(default='gemini-2.5-flash-lite', min_length=1)

    # --- Generales ---
    LOG_LEVEL: str = 'INFO'
    MAX_RETRIES: int = 2
    REQUEST_TIMEOUT: int = 120

    # --- OCR ---
    TESSERACT_PATH: Path
    POPPLER_PATH: Path

    # --- Supabase (almacenamiento) ---
    SUPABASE_URL: HttpUrl
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = 'documentos'

    @property
    def lista_llaves(self) -> list[str]:
        return [llave.strip() for llave in self.GOOGLE_API_KEYS.split(',') if llave.strip()]

    @model_validator(mode='after')
    def validar_proveedor(self):
        proveedor = self.AI_PROVIDER.lower().strip()
        if proveedor not in {'ollama', 'gemini'}:
            raise ValueError(f"AI_PROVIDER inválido: '{self.AI_PROVIDER}'. Use 'ollama' o 'gemini'.")
        if proveedor == 'gemini' and not self.lista_llaves:
            raise ValueError("AI_PROVIDER='gemini' requiere al menos una llave en GOOGLE_API_KEYS.")
        return self

    @field_validator('TESSERACT_PATH')
    @classmethod
    def validar_tesseract(cls, v: Path):
        if sys.platform.startswith('win'):
            if not v.exists():
                raise ValueError(f'TESSERACT_PATH no existe: {v}')
            if not v.is_file():
                raise ValueError('TESSERACT_PATH debe ser un archivo .exe')
        elif not v.exists():
            raise ValueError(f"TESSERACT_PATH no existe: {v}. Instala con 'apt-get install tesseract-ocr'")
        return v

    @field_validator('POPPLER_PATH')
    @classmethod
    def validar_poppler(cls, v: Path):
        if sys.platform.startswith('win'):
            if not v.exists():
                raise ValueError(f'POPPLER_PATH no existe: {v}')
            if not v.is_dir():
                raise ValueError('POPPLER_PATH debe ser un directorio')
        elif not v.exists():
            raise ValueError(f"POPPLER_PATH no existe: {v}. Instala con 'apt-get install poppler-utils'")
        return v

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True, extra='forbid')

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
