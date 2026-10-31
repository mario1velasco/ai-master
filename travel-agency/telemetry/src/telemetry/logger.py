"""Log de aplicación: el `get_logger` del tema 4 con el trace_id en cada línea y un archivo rotado por componente."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from telemetry.config import get_config
from telemetry.context import current_trace_id

_FORMATTER = logging.Formatter("%(asctime)s %(levelname)s %(name)s [%(trace_id)s]: %(message)s")
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3

# Un solo RotatingFileHandler por archivo: si dos handlers rotan el mismo archivo, se pisan.
_file_handlers: dict[Path, RotatingFileHandler] = {}


class _TraceIdFilter(logging.Filter):
    """Añade el trace_id activo a cada línea ('-' si no hay span abierto)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = current_trace_id() or "-"
        return True


class _ComponentFileHandler(logging.Handler):
    """Escribe en `<log_dir>/<componente>/app.log`, leyendo log_dir en cada línea por si se ha reconfigurado."""

    def __init__(self, component: str) -> None:
        super().__init__()
        self._component = component

    def emit(self, record: logging.LogRecord) -> None:
        path = get_config().log_dir / self._component / "app.log"
        handler = _file_handlers.get(path)
        if handler is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8")
            handler.setFormatter(_FORMATTER)
            _file_handlers[path] = handler
        handler.handle(record)


def get_logger(name: str) -> logging.Logger:
    """Logger con salida por consola y a `<log_dir>/<componente>/app.log`.

    El componente es la primera parte del nombre: `get_logger("text2sql.validar")` escribe en `text2sql/`.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(_FORMATTER)
        file = _ComponentFileHandler(name.split(".")[0])
        for handler in (console, file):
            handler.addFilter(_TraceIdFilter())
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        # Sin propagar: si un padre ('text2sql') y un hijo ('text2sql.validar') tienen handlers, se duplicarían.
        logger.propagate = False
    return logger


def close_log_files() -> None:
    """Cierra los archivos de log abiertos (para los tests, que cambian de carpeta en cada uno)."""
    for handler in _file_handlers.values():
        handler.close()
    _file_handlers.clear()
