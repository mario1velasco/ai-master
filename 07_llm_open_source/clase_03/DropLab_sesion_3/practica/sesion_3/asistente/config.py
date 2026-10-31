"""Rutas, direcciones y modelos del asistente. Todo se puede cambiar con variables de entorno.

    DROPLAB_OLLAMA          dirección de Ollama                (http://127.0.0.1:11434)
    DROPLAB_MODELO_TEXTO    modelo que planifica y redacta      (qwen3:30b-a3b-instruct-2507-q4_K_M)
    DROPLAB_MODELO_VISION   modelo que lee las imágenes (VLM)   (qwen3-vl:8b-instruct)
    DROPLAB_API             dirección de la API de la sesión 3  (http://127.0.0.1:8000)
    DROPLAB_INDICE          ampliado (sesión 2 + junio) o sesion2  (ampliado, si existe)

Configuración ligera para un portátil de 16 GB (medida en docs/sesion_3/04):
    DROPLAB_MODELO_TEXTO=qwen3:4b-instruct  DROPLAB_MODELO_VISION=qwen3-vl:4b-instruct
"""

from __future__ import annotations

import os
from pathlib import Path

ASISTENTE = Path(__file__).resolve().parent
SESION3 = ASISTENTE.parent
PRACTICA = SESION3.parent
ROOT = PRACTICA.parent
SESION1 = PRACTICA / "sesion_1"
SESION2 = PRACTICA / "sesion_2"

IMAGENES = ROOT / "data" / "imagenes"                  # las cuatro imágenes del caso (no se modifican)
SINTETICAS = SESION3 / "imagenes_sinteticas"           # derivadas para practicar (marcadas como sintéticas)
GUARDADAS = SESION3 / "salidas_guardadas"              # salidas reales guardadas: plan B si algo falla
RESULTADOS = ROOT / "experimentos" / "sesion_3"        # mediciones (evaluación y comparación)

OLLAMA_URL = os.environ.get("DROPLAB_OLLAMA", "http://127.0.0.1:11434").rstrip("/")
MODELO_TEXTO = os.environ.get("DROPLAB_MODELO_TEXTO", "qwen3:30b-a3b-instruct-2507-q4_K_M")
MODELO_VISION = os.environ.get("DROPLAB_MODELO_VISION", "qwen3-vl:8b-instruct")
API_URL = os.environ.get("DROPLAB_API", "http://127.0.0.1:8000").rstrip("/")

KEEP_ALIVE = os.environ.get("DROPLAB_KEEP_ALIVE", "30m")   # que Ollama no descargue los modelos entre demos

# El índice de documentos: el AMPLIADO (sesión 2 + los PDF de junio, 09_indice_junio.py) si existe; si no, el de la
# sesión 2. DROPLAB_INDICE=sesion2 fuerza el de la sesión 2 (así se reproducen las salidas guardadas antes de junio).
RAG3 = SESION3 / "rag"
INDICE_AMPLIADO = RAG3 / "indice_ampliado_bge-m3.duckdb"
CORPUS_AMPLIADO = RAG3 / "corpus_ampliado.jsonl"
INDICE = os.environ.get("DROPLAB_INDICE", "ampliado")
# Un único tamaño de contexto por modelo: si una llamada pide otro num_ctx, Ollama RECARGA el modelo (medido: el plan
# con 2.048 y la redacción con 12.288 costaban ~25 s de recarga en cada pregunta).
CTX_TEXTO = 12288
CTX_VISION = 8192

MAX_LADO_IMAGEN = 1024        # se reduce la imagen a 1024 px de lado: 1.084 tokens en lugar de 1.582 (medido)
MAX_BYTES_IMAGEN = 15_000_000
