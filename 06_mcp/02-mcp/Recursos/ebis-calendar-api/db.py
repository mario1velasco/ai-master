"""Pseudo-base de datos en memoria para trabajadores y reuniones."""

from datetime import date, datetime, time, timedelta
from typing import Any


WORK_START = time(9, 0)
WORK_END = time(17, 0)

WORKERS: list[dict[str, Any]] = [
    {"id": 1, "name": "Ana García", "role": "Desarrolladora"},
    {"id": 2, "name": "Luis Martín", "role": "Diseñador"},
    {"id": 3, "name": "Marta López", "role": "Product Manager"},
]


def _next_weekday(after: date) -> date:
    day = after + timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


_sample_day = _next_weekday(date.today())
MEETINGS: list[dict[str, Any]] = [
    {
        "id": 1,
        "worker_id": 1,
        "title": "Reunión de equipo",
        "start": datetime.combine(_sample_day, time(10, 0)),
        "end": datetime.combine(_sample_day, time(10, 30)),
    },
    {
        "id": 2,
        "worker_id": 1,
        "title": "Planificación",
        "start": datetime.combine(_sample_day, time(11, 0)),
        "end": datetime.combine(_sample_day, time(12, 0)),
    },
    {
        "id": 3,
        "worker_id": 2,
        "title": "Revisión de diseño",
        "start": datetime.combine(_sample_day, time(9, 30)),
        "end": datetime.combine(_sample_day, time(10, 0)),
    },
]


def list_workers() -> list[dict[str, Any]]:
    return WORKERS.copy()


def get_worker(worker_id: int) -> dict[str, Any] | None:
    return next((worker for worker in WORKERS if worker["id"] == worker_id), None)


def list_meetings(worker_id: int, day: date | None = None) -> list[dict[str, Any]]:
    return [
        meeting
        for meeting in MEETINGS
        if meeting["worker_id"] == worker_id
        and (day is None or meeting["start"].date() == day)
    ]


def meeting_overlaps(worker_id: int, start: datetime, end: datetime) -> bool:
    return any(
        meeting["worker_id"] == worker_id
        and start < meeting["end"]
        and end > meeting["start"]
        for meeting in MEETINGS
    )


def create_meeting(
    worker_id: int,
    title: str,
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    meeting = {
        "id": max((item["id"] for item in MEETINGS), default=0) + 1,
        "worker_id": worker_id,
        "title": title,
        "start": start,
        "end": end,
    }
    MEETINGS.append(meeting)
    return meeting
