"""`span()`: cronometra un bloque, captura errores y escribe su evento al cerrar."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any

from pydantic import ValidationError

from contracts.metrics import BaseMetrics, Component, Status, Versions, short_hash
from telemetry.config import get_config
from telemetry.context import current_span, current_trace, new_span_id, new_trace_id
from telemetry.event import Event
from telemetry.logger import get_logger
from telemetry.writer import write_event

_ERROR_MESSAGE_CHARS = 500

logger = get_logger("telemetry.span")


@dataclass(slots=True)
class Span:
    """Lo que el bloque puede rellenar mientras se ejecuta; al cerrar se convierte en métricas.

    Attributes:
        output_text: Salida del paso. Solo se guardan su longitud, nunca el texto.
        fields: Campos propios de la clase de métricas (p. ej. `model`, `input_tokens` de LlmCallMetrics).
        attributes: Métricas libres, sin cambiar el esquema.
        metrics: Las métricas ya validadas; se rellena al cerrar el span, para devolverlas en el resultado.
    """

    name: str
    component: Component
    trace_id: str
    span_id: str
    parent_span_id: str | None
    started_at: datetime
    input_text: str | None = None
    output_text: str | None = None
    versions: Versions | None = None
    fields: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, str | int | float | bool] = field(default_factory=dict)
    status: Status = Status.ok
    error_type: str | None = None
    error_message: str | None = None
    metrics: BaseMetrics | None = None

    def reject(self, reason: str) -> None:
        """Marca el paso como rechazado sin lanzar excepción (p. ej. el validador bloquea un DROP)."""
        self.status = Status.rejected
        self.error_type = reason

    def base_fields(self, latency_ms: float) -> dict[str, Any]:
        """Campos de BaseMetrics que salen del propio span."""
        data: dict[str, Any] = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "component": self.component,
            "name": self.name,
            "started_at": self.started_at,
            # Desde started_at y no con otro now(): si el reloj del sistema salta, ended_at no queda antes.
            "ended_at": self.started_at + timedelta(milliseconds=latency_ms),
            "latency_ms": latency_ms,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "attributes": self.attributes,
        }
        if self.input_text is not None:
            data["input_chars"] = len(self.input_text)
            data["input_hash"] = short_hash(self.input_text)
        if self.output_text is not None:
            data["output_chars"] = len(self.output_text)
        if self.versions is not None:
            data["versions"] = self.versions
        return data


@contextmanager
def span(
    name: str,
    *,
    component: Component,
    metrics_cls: type[BaseMetrics] = BaseMetrics,
    input_text: str | None = None,
    versions: Versions | None = None,
    trace_id: str | None = None,
) -> Generator[Span]:
    """Abre un paso de la traza.

    Si no hay traza activa, empieza una (con `trace_id` si se pasa, como hará la API). Si la hay, este paso
    cuelga del span abierto. Una excepción del bloque deja el evento con `status=error` y se vuelve a lanzar.

    Example:
        >>> with span("sql.validar", component=Component.text2sql, input_text=sql) as s:
        ...     s.output_text = validar(sql)
    """
    s = Span(
        name=name,
        component=component,
        trace_id=trace_id or current_trace.get() or new_trace_id(),
        span_id=new_span_id(),
        parent_span_id=current_span.get(),
        started_at=datetime.now(UTC),
        input_text=input_text,
        versions=versions,
    )
    trace_token = current_trace.set(s.trace_id)
    span_token = current_span.set(s.span_id)
    start = perf_counter()
    try:
        yield s
    except BaseException as exc:
        s.status = Status.error
        s.error_type = type(exc).__name__
        s.error_message = str(exc)[:_ERROR_MESSAGE_CHARS] or None
        raise
    finally:
        latency_ms = round((perf_counter() - start) * 1000, 3)
        current_span.reset(span_token)
        current_trace.reset(trace_token)
        _close(s, metrics_cls, latency_ms)


def _close(s: Span, metrics_cls: type[BaseMetrics], latency_ms: float) -> None:
    config = get_config()
    try:
        s.metrics = _build_metrics(s, metrics_cls, latency_ms)
        write_event(Event.from_metrics(s.metrics, environment=config.environment))
    except (ValidationError, OSError):
        if config.strict:
            raise
        # La telemetría nunca rompe la petición: se pierde el evento, pero queda en el log.
        logger.exception("No se pudo registrar el span %s", s.name)


def _build_metrics(s: Span, metrics_cls: type[BaseMetrics], latency_ms: float) -> BaseMetrics:
    base = s.base_fields(latency_ms)
    try:
        return metrics_cls.model_validate(base | s.fields)
    except ValidationError:
        if s.status is not Status.error or metrics_cls is BaseMetrics:
            raise
        # Una llamada que falló antes de tener tokens no puede llenar LlmCallMetrics. El evento de error es
        # el más importante, así que se guarda con BaseMetrics y se apunta qué clase se esperaba.
        base["attributes"] = s.attributes | {"expected_metrics_type": metrics_cls.__name__}
        return BaseMetrics.model_validate(base)
