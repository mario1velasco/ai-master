"""Los módulos de las sesiones 1 y 2, importados tal cual (sin copiarlos ni cambiarlos).

Sus nombres empiezan por un número (02_capa_semantica.py…), así que se importan con import_module,
como hacen entre ellos los scripts de la sesión 2.
"""

from __future__ import annotations

import sys
from importlib import import_module

from . import config

for _ruta in (config.SESION1, config.SESION2):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

capa = import_module("02_capa_semantica")              # vistas con el negocio dentro + barreras del SQL
preguntar_datos = import_module("01_preguntar_datos")   # el modelo escribe SQL; el código lo ejecuta y verifica cifras
indice = import_module("11_indice")                      # embeddings (bge-m3) en DuckDB
buscar = import_module("12_buscar")                      # búsqueda híbrida + regla de versiones
rag = import_module("13_preguntar_documentos")           # respuesta con [F#] y verificación
