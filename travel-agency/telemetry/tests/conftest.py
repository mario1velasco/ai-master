from collections.abc import Iterator
from pathlib import Path

import pytest

from telemetry import close_log_files, configure, get_config


@pytest.fixture(autouse=True)
def log_dir(tmp_path: Path) -> Iterator[Path]:
    """Cada test escribe en su carpeta temporal, en modo estricto, y deja la configuración como estaba."""
    previous = get_config()
    configure(log_dir=tmp_path, environment="test", strict=True)
    yield tmp_path
    close_log_files()
    configure(log_dir=previous.log_dir, environment=previous.environment, strict=previous.strict)
