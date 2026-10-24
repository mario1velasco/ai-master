"""Modelo para LangChain / LangGraph (sesiones 3 a 6), con la misma configuración del .env."""
from langchain_openai import ChatOpenAI

from comun.llm import API_KEY, BASE_URL, MODELO


def crear_modelo(temperatura: float = 0) -> ChatOpenAI:
    return ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODELO, temperature=temperatura)
