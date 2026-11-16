"""Lo que recibe el modelo: instrucciones + esquema generado + guía.

Como `construir_system_prompt()` de
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py`. El esquema y la guía son los
de `database` (nadie los escribe a mano aquí). Desvío: las `INSTRUCCIONES` de clase sin la parte de redactar
(eso lo hace el agente) y sin `PERIODOS` (Viajes Nimbo no tiene periodos A/B).
"""

import duckdb

from database.schema import cached_schema
from database.semantic_layer import GUIDE

PROMPT_VERSION = "text2sql_prompt_v4"  # va en las Versions de las métricas: cámbiala si cambias el prompt

INSTRUCTIONS = """Eres el analista de datos de Viajes Nimbo. Tienes una base DuckDB de solo lectura.
Para obtener cualquier cifra usa la herramienta run_sql con UNA consulta SELECT.
No inventes vistas ni columnas. Si run_sql da error, vuelve a llamar a run_sql con la consulta corregida: no escribas
el SQL en el texto ni digas que el dato no existe. Casi siempre es una columna tomada de la vista que no la tiene.
Haz TODAS las operaciones (sumas, restas, divisiones) dentro del SQL; no calcules de cabeza.
Si la pregunta compara varios clientes, reservas o vuelos, obtén cada valor y etiquétalo.
Si la pregunta pide un dato que no existe en las vistas, dilo claramente en lugar de aproximarlo; no respondas con
otro dato parecido en su lugar.
Filtra solo por lo que pide la pregunta: no añadas condiciones que no pide.
Si mezclas AND y OR, pon paréntesis.
Al unir vistas, toma cada columna de la vista que la tiene.
Si un nombre es de varios clientes, devuelve las filas de todos, cada una con su cliente_id; no preguntes cuál."""


def build_system_prompt(con: duckdb.DuckDBPyConnection) -> str:
    """En cada pregunta, como en clase. El esquema sale de `cached_schema()`, guardado por huella en memoria y en
    disco (TRAVEL-009): aquí no se guarda nada, así la conexión se libera cuando quien la abrió deja de usarla.
    """
    return "\n\n".join([INSTRUCTIONS, cached_schema(con), GUIDE])
