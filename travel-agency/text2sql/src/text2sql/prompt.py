"""Lo que recibe el modelo: instrucciones + esquema generado + guía.

Como `construir_system_prompt()` de
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py`. El esquema y la guía son los
de `database` (nadie los escribe a mano aquí). Desvío: las `INSTRUCCIONES` de clase sin la parte de redactar
(eso lo hace el agente) y sin `PERIODOS` (Viajes Nimbo no tiene periodos A/B).
"""

from functools import cache

import duckdb

from database.semantic_layer import GUIDE, schema

PROMPT_VERSION = "text2sql_prompt_v1"  # va en las Versions de las métricas: cámbiala si cambias el prompt

INSTRUCTIONS = """Eres el analista de datos de Viajes Nimbo. Tienes una base DuckDB de solo lectura.
Para obtener cualquier cifra usa la herramienta run_sql con UNA consulta SELECT.
No inventes vistas ni columnas. Si la consulta da error, corrígela.
Haz TODAS las operaciones (sumas, restas, divisiones) dentro del SQL; no calcules de cabeza.
Si la pregunta compara varios clientes, reservas o vuelos, obtén cada valor y etiquétalo.
Si la pregunta pide un dato que no existe en las vistas, dilo claramente en lugar de aproximarlo."""


@cache
def build_system_prompt(con: duckdb.DuckDBPyConnection) -> str:
    """Una vez por conexión. Desvío: en clase se genera en cada pregunta, pero `schema()` tarda ~5 s y la base
    es de solo lectura, así que el esquema no cambia mientras el proceso vive (acordado con Mario).

    La caché guarda cada conexión con su prompt mientras el proceso vive. Basta con una conexión por proceso
    (el comando, la API).
    """
    return "\n\n".join([INSTRUCTIONS, schema(con), GUIDE])
