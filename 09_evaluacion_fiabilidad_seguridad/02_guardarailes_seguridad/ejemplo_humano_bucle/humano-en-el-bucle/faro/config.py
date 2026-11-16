"""Configuración: modelo de lenguaje y rutas de los datos.

Igual que en el resto del Tema 8, el modelo se elige en el archivo .env: Ollama en
local por defecto o cualquier proveedor compatible con la API de OpenAI.
"""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv(usecwd=True))

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")  # Ollama ignora la clave, pero la librería la exige
MODELO = os.getenv("LLM_MODEL", "qwen2.5:7b")

RAIZ = Path(__file__).resolve().parent.parent
RUTA_BD = RAIZ / "datos" / "faro.sqlite"      # estado del equipo (checkpoints) y registro de encargos
CARPETA_BUZON = RAIZ / "buzon"                 # emails simulados que recibe la persona
CARPETA_ENTREGAS = RAIZ / "entregas"           # propuestas terminadas
URL_BANDEJA = os.getenv("URL_BANDEJA", "http://127.0.0.1:8000")


def crear_modelo(temperatura: float = 0) -> ChatOpenAI:
    return ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODELO, temperature=temperatura)
