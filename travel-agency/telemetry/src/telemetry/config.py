"""Configuración de la telemetría: dónde se escribe, en qué entorno y si los fallos propios se lanzan."""

from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TelemetryConfig:
    """Valores activos de la telemetría.

    Attributes:
        log_dir: Carpeta raíz de los logs; dentro va una carpeta por componente.
        environment: Entorno que se apunta en cada evento (`local`, `test`…).
        strict: Si es True, un fallo de la propia telemetría (métrica inválida, disco lleno) se lanza.
            Si es False, se registra en el log y la petición sigue. Los tests lo activan.
    """

    log_dir: Path = Path("logs")
    environment: str = "local"
    strict: bool = False


_config = TelemetryConfig()


def configure(*, log_dir: Path | str | None = None, environment: str | None = None, strict: bool | None = None) -> None:
    """Cambia solo los valores que se pasan; el resto se queda como estaba."""
    global _config
    changes: dict[str, object] = {}
    if log_dir is not None:
        changes["log_dir"] = Path(log_dir)
    if environment is not None:
        changes["environment"] = environment
    if strict is not None:
        changes["strict"] = strict
    _config = replace(_config, **changes)


def get_config() -> TelemetryConfig:
    """Devuelve la configuración activa."""
    return _config
