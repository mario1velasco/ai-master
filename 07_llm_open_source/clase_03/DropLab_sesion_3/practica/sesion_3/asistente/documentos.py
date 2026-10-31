"""Los documentos: el RAG de la sesión 2, sin cambios (12_buscar.py y 13_preguntar_documentos.py).

El índice: el AMPLIADO (practica/sesion_3/rag/, 09_indice_junio.py) = los 51 fragmentos de la sesión 2, con los
mismos id, + las páginas de los PDF de junio leídas por PaddleOCR-VL. Si no existe (o DROPLAB_INDICE=sesion2),
el de la sesión 2 (bge-m3 en DuckDB, practica/sesion_2/rag/). Open WebUI no indexa nada: así no hay un segundo
RAG que trocee distinto o se salte la regla de versiones.
"""

from __future__ import annotations

import json
import threading

import requests

from . import config
from .ollama import ErrorComponente
from .sesion2 import buscar as _buscar
from .sesion2 import indice, rag

_b = None
_lock = threading.Lock()
CAMPOS = ("id", "cita", "fuente", "tipo", "titulo", "codigo", "seccion", "pagina", "fecha", "estado", "sustituido_por",
          "responsable", "lectura", "texto", "puntuacion", "anadido")


def ruta_indice():
    """El índice que se usa: el ampliado si existe y no se pide el de la sesión 2."""
    if config.INDICE != "sesion2" and config.INDICE_AMPLIADO.exists():
        return config.INDICE_AMPLIADO
    return indice.ruta_indice(indice.MODELO)


def buscador():
    global _b
    with _lock:
        if _b is None:
            try:
                _b = _buscar.Buscador(ruta=ruta_indice())
            except SystemExit as exc:          # la sesión 2 sale con SystemExit si falta el índice
                raise ErrorComponente("INDICE_NO_DISPONIBLE", "rag", str(exc))
    return _b


def _protegido(func, *args, **kw):
    try:
        with _lock:                            # una conexión DuckDB por proceso: una búsqueda cada vez
            return func(*args, **kw)
    except requests.exceptions.ConnectionError:
        raise ErrorComponente("OLLAMA_NO_DISPONIBLE", "ollama", "No responde Ollama: no se puede calcular el embedding.")
    except SystemExit as exc:
        raise ErrorComponente("MODELO_NO_INSTALADO", "ollama", str(exc))


def buscar(pregunta: str, k: int = 5, modo: str = "hibrida", vigentes: bool = True) -> list[dict]:
    """Los k fragmentos más relevantes (búsqueda híbrida) + el vigente si sale un sustituido."""
    if modo not in ("semantica", "palabras", "hibrida"):
        raise ErrorComponente("PARAMETRO_NO_VALIDO", "rag", f"Modo {modo!r}: semantica, palabras o hibrida.")
    frags = _protegido(buscador().buscar, pregunta, modo, k, vigentes)
    return [{c: f.get(c) for c in CAMPOS} for f in frags]


def preguntar(pregunta: str, k: int = 5, modelo: str | None = None) -> dict:
    """La respuesta con [F#] de la sesión 2, con su verificación."""
    b = buscador()
    try:
        r = rag.preguntar(pregunta, b, llm=modelo or config.MODELO_TEXTO, k=k)
    except requests.exceptions.ConnectionError:
        raise ErrorComponente("OLLAMA_NO_DISPONIBLE", "ollama", "No responde Ollama.")
    return {"respuesta": r["respuesta"], "avisos": r["avisos"], "segundos": r["segundos"],
            "fuentes": [{c: f.get(c) for c in CAMPOS if c != "texto"} for f in r["citados"]],
            "fragmentos": [{c: f.get(c) for c in CAMPOS} for f in r["fragmentos"]]}


def fragmento_por_codigo(codigo: str, contiene: str = "") -> dict | None:
    """Un fragmento del corpus por su código de documento (y un texto que debe contener)."""
    for f in buscador().frags.values():
        if f["codigo"] == codigo and contiene in f["texto"]:
            return {c: f.get(c) for c in CAMPOS}
    return None


def estado() -> dict:
    ruta = ruta_indice()
    corpus = config.CORPUS_AMPLIADO if ruta == config.INDICE_AMPLIADO else indice.CORPUS
    n = sum(1 for _ in corpus.open(encoding="utf-8")) if corpus.exists() else 0
    return {"ok": ruta.exists(), "indice": str(ruta.relative_to(config.ROOT)), "fragmentos": n,
            "modelo_embeddings": indice.MODELO, "ampliado": ruta == config.INDICE_AMPLIADO}


def resumen(f: dict) -> str:
    return json.dumps({k: f.get(k) for k in ("cita", "estado", "fecha", "sustituido_por")}, ensure_ascii=False)
