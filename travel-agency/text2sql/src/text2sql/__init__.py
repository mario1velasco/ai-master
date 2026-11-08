"""Pregunta → SQL validado y ejecutado sobre las vistas."""

from text2sql.loop import ask
from text2sql.ollama import ComponentError

__all__ = ["ComponentError", "ask"]
__version__ = "0.1.0"
