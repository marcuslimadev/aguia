"""
Configuração centralizada de logging
"""
import logging
import logging.handlers
from pathlib import Path
from config.config import LOGS_DIR, LOG_LEVEL, LOG_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logger(name: str) -> logging.Logger:
    """Configura um logger para um módulo"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Handler para arquivo
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Adicionar handlers
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtém ou cria um logger"""
    return setup_logger(name)
