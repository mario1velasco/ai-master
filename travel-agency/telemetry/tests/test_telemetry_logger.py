from pathlib import Path

from contracts.metrics import Component
from telemetry import get_logger, span


def test_logger_writes_trace_id_in_each_line(log_dir: Path) -> None:
    logger = get_logger("text2sql.validar")

    logger.info("fuera de traza")
    with span("sql.validar", component=Component.text2sql) as s:
        logger.info("dentro de traza")

    lines = (log_dir / "text2sql" / "app.log").read_text(encoding="utf-8").splitlines()
    assert "INFO text2sql.validar [-]: fuera de traza" in lines[0]
    assert f"INFO text2sql.validar [{s.trace_id}]: dentro de traza" in lines[1]


def test_logger_is_not_duplicated(log_dir: Path) -> None:
    parent = get_logger("rag")
    child = get_logger("rag.buscar")

    assert get_logger("rag") is parent
    child.info("una sola vez")

    content = (log_dir / "rag" / "app.log").read_text(encoding="utf-8")
    assert content.count("una sola vez") == 1
