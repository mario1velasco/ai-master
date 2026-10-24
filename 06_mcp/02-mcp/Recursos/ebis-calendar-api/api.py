"""Inicialización de FastAPI y endpoints de EBIS Calendar API."""

from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

import db


app = FastAPI(
    title="EBIS Calendar API",
    description="API de ejemplo para consultar trabajadores y gestionar reuniones.",
    version="0.1.0",
)


class MeetingCreate(BaseModel):
    worker_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=100)
    start: datetime
    end: datetime


def _get_worker_or_404(worker_id: int) -> dict:
    worker = db.get_worker(worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail=f"No existe el trabajador {worker_id}")
    return worker


def _worker_with_hours(worker: dict) -> dict:
    return {
        **worker,
        "working_days": "lunes a viernes",
        "work_start": db.WORK_START.strftime("%H:%M"),
        "work_end": db.WORK_END.strftime("%H:%M"),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/workers")
def list_workers() -> list[dict]:
    """Devuelve los trabajadores y su horario laboral habitual."""
    return [_worker_with_hours(worker) for worker in db.list_workers()]


@app.get("/workers/{worker_id}")
def get_worker(worker_id: int) -> dict:
    """Devuelve los datos de un trabajador."""
    return _worker_with_hours(_get_worker_or_404(worker_id))


@app.get("/workers/{worker_id}/meetings")
def get_worker_meetings(
    worker_id: int,
    day: date | None = Query(default=None, description="Filtra por día (AAAA-MM-DD)"),
) -> dict:
    """Lista las reuniones de un trabajador, opcionalmente para un día."""
    worker = _get_worker_or_404(worker_id)
    meetings = db.list_meetings(worker_id, day)
    return {"worker": worker, "day": day.isoformat() if day else None, "meetings": meetings}


@app.post("/meetings", status_code=status.HTTP_201_CREATED)
def create_meeting(request: MeetingCreate) -> dict:
    """Crea una reunión en horario laboral si no se solapa con otra."""
    _get_worker_or_404(request.worker_id)

    if request.start.tzinfo is not None or request.end.tzinfo is not None:
        raise HTTPException(
            status_code=422,
            detail="Usa fecha y hora local sin zona horaria, por ejemplo 2026-10-01T10:00:00",
        )
    if request.start >= request.end:
        raise HTTPException(status_code=422, detail="'start' debe ser anterior a 'end'")
    if request.start.date() != request.end.date():
        raise HTTPException(status_code=422, detail="La reunión debe empezar y terminar el mismo día")
    if request.start.weekday() >= 5:
        raise HTTPException(status_code=422, detail="Solo se permiten reuniones de lunes a viernes")
    if request.start.time() < db.WORK_START or request.end.time() > db.WORK_END:
        raise HTTPException(status_code=422, detail="El horario laboral es de 09:00 a 17:00")
    if db.meeting_overlaps(request.worker_id, request.start, request.end):
        raise HTTPException(status_code=409, detail="El trabajador ya tiene una reunión en ese horario")

    return db.create_meeting(
        worker_id=request.worker_id,
        title=request.title,
        start=request.start,
        end=request.end,
    )
