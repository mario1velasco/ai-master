"""Conexión con el modelo de lenguaje.

Todas las demos usan la API compatible con OpenAI, que ofrecen tanto Ollama
(en local) como la mayoría de proveedores en la nube. Para cambiar de modelo
o de proveedor basta con editar el archivo .env; el código no cambia.
"""
import os

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

load_dotenv(find_dotenv(usecwd=True))

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")  # Ollama ignora la clave, pero la librería la exige
MODELO = os.getenv("LLM_MODEL", "qwen2.5:7b")


def crear_cliente() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)
