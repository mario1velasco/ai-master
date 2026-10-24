"""Paso 7 · Celda `index`: fragmentar + InMemoryVectorStore (con embeddings falsos, sin red)."""
import contextlib
import io
import unittest

from langchain_core.embeddings import DeterministicFakeEmbedding

from tests.ayudas import PDF, cargar_funciones, celda_por_etiqueta, fuente
from utilidades import cargar_paginas


class Paso07Indice(unittest.TestCase):
    def test_indice_con_todos_los_fragmentos(self):
        espacio = cargar_funciones("fragmentar")
        espacio["paginas"], _ = cargar_paginas(PDF)
        espacio["embeddings"] = DeterministicFakeEmbedding(size=64)        # sustituye a la API
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(fuente(celda_por_etiqueta("index")), "<index>", "exec"), espacio)
        self.assertEqual(len(espacio["fragmentos"]), 33)
        self.assertEqual(len(espacio["indice"].store), len(espacio["fragmentos"]))

    def test_la_celda_solo_indexa_una_vez(self):
        self.assertEqual(fuente(celda_por_etiqueta("index")).count("add_documents"), 1)


if __name__ == "__main__":
    unittest.main()
