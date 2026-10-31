"""Cliente mínimo de Ollama: una llamada, sus tiempos y errores con nombre.

Se usa requests (como en las sesiones 1 y 2) para ver exactamente qué se envía. LangChain ofrece
integraciones equivalentes (ChatOllama), pero aquí no hacen falta.

Tiempos que devuelve cada llamada (los da Ollama):
    segundos_carga     cargar el modelo en memoria (0 si ya estaba cargado)
    segundos_entrada   procesar el prompt (texto e imagen)
    segundos_salida    escribir la respuesta, token a token
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from . import config


class ErrorComponente(Exception):
    """Un error que dice qué pieza ha fallado. La API lo devuelve tal cual en «errores»."""

    def __init__(self, codigo: str, componente: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo, self.componente, self.mensaje = codigo, componente, mensaje

    def como_dict(self) -> dict:
        return {"codigo": self.codigo, "componente": self.componente, "mensaje": self.mensaje}


@dataclass
class Respuesta:
    contenido: str
    modelo: str
    segundos: float
    segundos_carga: float
    segundos_entrada: float
    segundos_salida: float
    tokens_entrada: int
    tokens_salida: int

    @property
    def tokens_por_segundo(self) -> float:
        return round(self.tokens_salida / self.segundos_salida, 1) if self.segundos_salida else 0.0

    def tiempos(self) -> dict:
        return {"modelo": self.modelo, "segundos": round(self.segundos, 1), "carga": round(self.segundos_carga, 1),
                "entrada": round(self.segundos_entrada, 1), "salida": round(self.segundos_salida, 1),
                "tokens_entrada": self.tokens_entrada, "tokens_salida": self.tokens_salida,
                "tokens_por_segundo": self.tokens_por_segundo}


def chat(modelo: str, mensajes: list[dict], formato: dict | str | None = None, num_ctx: int = 8192,
         num_predict: int = 1024, temperatura: float = 0.0, timeout: int = 600, url: str | None = None) -> Respuesta:
    """Una llamada a /api/chat sin streaming. formato: un esquema JSON (salida estructurada) o None."""
    url = (url or config.OLLAMA_URL) + "/api/chat"
    payload = {"model": modelo, "messages": mensajes, "stream": False, "think": False, "keep_alive": config.KEEP_ALIVE,
               "options": {"temperature": temperatura, "num_ctx": num_ctx, "num_predict": num_predict}}
    if formato is not None:
        payload["format"] = formato
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError:
        raise ErrorComponente("OLLAMA_NO_DISPONIBLE", "ollama",
                              f"No hay respuesta de Ollama en {url}. ¿Está en marcha? (systemctl status ollama)")
    except requests.exceptions.Timeout:
        raise ErrorComponente("OLLAMA_TIEMPO_AGOTADO", "ollama", f"{modelo} no respondió en {timeout} s.")
    if r.status_code == 404:
        raise ErrorComponente("MODELO_NO_INSTALADO", "ollama", f"Ollama no tiene el modelo {modelo}: ollama pull {modelo}")
    if r.status_code != 200:
        raise ErrorComponente("OLLAMA_ERROR", "ollama", f"Ollama devolvió {r.status_code}: {r.text[:300]}")
    j = r.json()
    return Respuesta(contenido=(j.get("message") or {}).get("content", ""), modelo=modelo,
                     segundos=time.time() - t0, segundos_carga=j.get("load_duration", 0) / 1e9,
                     segundos_entrada=j.get("prompt_eval_duration", 0) / 1e9,
                     segundos_salida=j.get("eval_duration", 0) / 1e9,
                     tokens_entrada=j.get("prompt_eval_count", 0) or 0, tokens_salida=j.get("eval_count", 0) or 0)


def estado(url: str | None = None) -> dict:
    """¿Responde Ollama? ¿Qué modelos tiene instalados y cuáles están cargados en memoria?"""
    url = url or config.OLLAMA_URL
    try:
        instalados = [m["name"] for m in requests.get(url + "/api/tags", timeout=5).json().get("models", [])]
        cargados = [{"modelo": m["name"], "gb": round(m.get("size", 0) / 1e9, 1)}
                    for m in requests.get(url + "/api/ps", timeout=5).json().get("models", [])]
        return {"ok": True, "url": url, "instalados": instalados, "cargados": cargados}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: no responde"}
