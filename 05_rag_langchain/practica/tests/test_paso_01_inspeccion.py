"""Paso 1 · Inspección de la carga: páginas físicas, página 7 sin texto, metadatos."""
import unittest

from utilidades import cargar_paginas

from tests.ayudas import PDF, leer_notebook


class Paso01Inspeccion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paginas, cls.info = cargar_paginas(PDF)

    def test_resumen_de_extraccion(self):
        self.assertEqual(self.info, {"paginas_pdf": 25, "paginas_con_texto": 24, "paginas_sin_texto": [7]})

    def test_numeracion_fisica_sin_renumerar(self):
        numeros = [d.metadata["page"] for d in self.paginas]
        self.assertEqual(numeros, [n for n in range(1, 26) if n != 7])

    def test_metadatos_de_cita(self):
        for d in self.paginas:
            self.assertEqual(d.metadata["source"], "TENERIFE.pdf")

    def test_paginas_de_referencia_tienen_los_datos(self):
        por_pagina = {d.metadata["page"]: d.page_content for d in self.paginas}
        self.assertIn("La Jardina", por_pagina[5])
        self.assertIn("TF24", por_pagina[15].replace("-", ""))
        self.assertIn("La Fogalera", por_pagina[25])
        self.assertIn("Las Vistas", por_pagina[23])

    def test_notebook_documenta_las_limitaciones(self):
        texto = " ".join("".join(c["source"]) for c in leer_notebook()["cells"] if c["cell_type"] == "markdown")
        for clave in ("página 7", "sin texto", "imágenes"):
            self.assertIn(clave, texto)


if __name__ == "__main__":
    unittest.main()
