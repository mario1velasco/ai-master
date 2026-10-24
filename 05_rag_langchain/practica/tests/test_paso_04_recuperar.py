"""Paso 4 · TODO 2 recuperar (celda `recuperar`) con embeddings deterministas (sin red)."""
import unittest

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore

from tests.ayudas import PDF, cargar_funciones
from utilidades import cargar_paginas


class Paso04Recuperar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        espacio = cargar_funciones("fragmentar", "recuperar")
        paginas, _ = cargar_paginas(PDF)
        cls.frags = espacio["fragmentar"](paginas, 900, 150)
        cls.indice = InMemoryVectorStore(embedding=DeterministicFakeEmbedding(size=64))
        cls.indice.add_documents(cls.frags)
        cls.recuperar = staticmethod(espacio["recuperar"])

    def test_devuelve_k_documentos(self):
        for k in (2, 4):
            self.assertEqual(len(self.recuperar(self.indice, "¿Qué mirador de Anaga?", k)), k)

    def test_devuelve_documents_con_metadatos_de_cita(self):
        for d in self.recuperar(self.indice, "Teide", 4):
            self.assertEqual(d.metadata["source"], "TENERIFE.pdf")
            self.assertIn("page", d.metadata)
            self.assertIn("chunk_id", d.metadata)

    def test_la_misma_pregunta_da_el_mismo_orden(self):
        a = [d.metadata["chunk_id"] for d in self.recuperar(self.indice, "playas", 4)]
        b = [d.metadata["chunk_id"] for d in self.recuperar(self.indice, "playas", 4)]
        self.assertEqual(a, b)

    def test_k2_son_los_dos_primeros_de_k4(self):
        a = [d.metadata["chunk_id"] for d in self.recuperar(self.indice, "arepas", 2)]
        b = [d.metadata["chunk_id"] for d in self.recuperar(self.indice, "arepas", 4)]
        self.assertEqual(a, b[:2])

    def test_k_invalido(self):
        with self.assertRaises(ValueError):
            self.recuperar(self.indice, "Teide", 0)

    def test_firma_no_admite_paginas_de_referencia(self):
        import inspect
        self.assertEqual(list(inspect.signature(self.recuperar).parameters), ["indice", "pregunta", "k"])


if __name__ == "__main__":
    unittest.main()
