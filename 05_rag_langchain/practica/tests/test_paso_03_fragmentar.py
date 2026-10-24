"""Paso 3 · TODO 1 fragmentar (celda `fragmentar`): metadatos, chunk_id único, tamaños."""
import unittest
from collections import Counter

from tests.ayudas import PDF, cargar_funciones, leer_notebook
from utilidades import cargar_paginas, construir_contexto


class Paso03Fragmentar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.espacio = cargar_funciones("fragmentar")
        cls.fragmentar = staticmethod(cls.espacio["fragmentar"])
        cls.tam, cls.sol = cls.espacio["CHUNK_SIZE"], cls.espacio["CHUNK_OVERLAP"]
        cls.paginas, _ = cargar_paginas(PDF)
        cls.frags = cls.fragmentar(cls.paginas, cls.tam, cls.sol)

    def test_parametros_del_enunciado(self):
        self.assertEqual((self.tam, self.sol), (900, 150))

    def test_conserva_source_y_page(self):
        paginas_validas = {d.metadata["page"] for d in self.paginas}
        for f in self.frags:
            self.assertEqual(f.metadata["source"], "TENERIFE.pdf")
            self.assertIn(f.metadata["page"], paginas_validas)

    def test_pagina_7_no_aparece(self):
        self.assertNotIn(7, {f.metadata["page"] for f in self.frags})

    def test_chunk_id_unico_y_no_vacio(self):
        ids = [f.metadata["chunk_id"] for f in self.frags]
        self.assertTrue(all(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_ningun_fragmento_supera_el_tamano(self):
        self.assertLessEqual(max(len(f.page_content) for f in self.frags), self.tam)

    def test_numero_plausible_de_fragmentos(self):
        self.assertTrue(30 <= len(self.frags) <= 45, len(self.frags))

    def test_cada_pagina_con_texto_tiene_al_menos_un_fragmento(self):
        self.assertEqual({f.metadata["page"] for f in self.frags}, {d.metadata["page"] for d in self.paginas})

    def test_no_se_pierde_texto_de_una_pagina_corta(self):
        pagina2 = next(d for d in self.paginas if d.metadata["page"] == 2)
        textos = [f.page_content for f in self.frags if f.metadata["page"] == 2]
        self.assertEqual(textos, [pagina2.page_content.strip()])

    def test_no_muta_las_paginas_originales(self):
        self.assertTrue(all("chunk_id" not in d.metadata for d in self.paginas))

    def test_construir_contexto_funciona(self):
        contexto = construir_contexto(self.frags[:2])
        self.assertIn("[TENERIFE.pdf, p.", contexto)
        self.assertIn("fragmento", contexto)

    def test_el_notebook_justifica_tamano_y_solape(self):
        texto = " ".join("".join(c["source"]) for c in leer_notebook()["cells"] if c["cell_type"] == "markdown")
        self.assertIn("900", texto)
        self.assertIn("150", texto)


if __name__ == "__main__":
    unittest.main()
