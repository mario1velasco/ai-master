"""Valores cerrados comunes a todas las métricas."""

from enum import StrEnum


class Status(StrEnum):
    """Cómo terminó un paso."""

    ok = "ok"
    error = "error"
    rejected = "rejected"


class Component(StrEnum):
    """Paquete o proceso que produjo la métrica."""

    api = "api"
    agent = "agent"
    text2sql = "text2sql"
    rag = "rag"
    database = "database"
    conversion = "conversion"
    eval = "eval"
    finetune = "finetune"
