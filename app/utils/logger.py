from __future__ import annotations
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
'\napp/utils/logger.py\n\nLogger configurable para la aplicación:\n- salida por consola (con colores opcional)\n- archivo rotativo (RotatingFileHandler)\n- evita duplicar handlers al recuperar el logger varias veces\n- niveles y formato configurables\n'
_LEVEL_COLORS = {'DEBUG': '\x1b[36m', 'INFO': '\x1b[32m', 'WARNING': '\x1b[33m', 'ERROR': '\x1b[31m', 'CRITICAL': '\x1b[41m'}
_RESET = '\x1b[0m'

class ColorfulFormatter(logging.Formatter):

    def __init__(self, fmt: str, datefmt: Optional[str]=None, use_color: bool=True):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_color = use_color and os.name != 'nt'

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if self.use_color and levelname in _LEVEL_COLORS:
            record.levelname = f'{_LEVEL_COLORS[levelname]}{levelname}{_RESET}'
        return super().format(record)

def get_logger(name: Optional[str]=None, *, level: Optional[int]=None, log_file: Optional[str]=None, rotate: bool=True, max_bytes: int=10 * 1024 * 1024, backup_count: int=5, console: bool=True, color: bool=True) -> logging.Logger:
    env_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    resolved_level = level if level is not None else getattr(logging, env_level, logging.INFO)
    logger_name = name if name else 'app'
    logger = logging.getLogger(logger_name)
    logger.setLevel(resolved_level)
    logger.propagate = False
    if logger.handlers:
        for h in logger.handlers:
            h.setLevel(resolved_level)
        return logger
    fmt = '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(resolved_level)
        ch_formatter = ColorfulFormatter(fmt=fmt, datefmt=datefmt, use_color=color)
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        if rotate:
            fh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
        else:
            fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(resolved_level)
        fh_formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
    return logger
logger = get_logger(__name__)
