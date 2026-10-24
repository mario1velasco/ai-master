"""Paso 10 · validar_conclusion con textos de ejemplo (la conclusión real se escribe con las cifras reales)."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from herramientas.validar_conclusion import extraer, validar

TABLA = """
| Métrica | k = 2 | k = 4 |
|---|---|---|
| Hit@k (Q1–Q4) | 3/4 | 4/4 |
| Respaldo | 3/4 | 3/4 |
| Citas | 3/4 | 4/4 |
| Abstención (Q5–Q6) | 2/2 | 2/2 |
"""


def texto_valido(relleno_palabras=300):
    relleno = " ".join(["palabra"] * relleno_palabras)
    return (f"### Conclusión\n\nSe fragmentó por página. {relleno}\n{TABLA}\nEn Q3 con k = 2 falló la recuperación. "
            "Recomiendo k = 4 para el piloto. Una limitación es el conjunto pequeño; una mejora propuesta es búsqueda híbrida.")


class Paso10Conclusion(unittest.TestCase):
    def test_texto_valido(self):
        self.assertEqual(validar(texto_valido()), [])

    def test_demasiado_corto(self):
        self.assertTrue(any("palabras" in p for p in validar(texto_valido(50))))

    def test_demasiado_largo(self):
        self.assertTrue(any("palabras" in p for p in validar(texto_valido(600))))

    def test_falta_tabla(self):
        self.assertTrue(any("tabla" in p for p in validar(texto_valido().replace(TABLA, ""))))

    def test_falta_caso_y_mejora(self):
        texto = re.sub(r"Q[1-6]", "esa pregunta", texto_valido()).replace("mejora", "idea")
        problemas = " ".join(validar(texto))
        self.assertIn("caso", problemas)
        self.assertIn("mejora", problemas)

    def test_sin_celda_de_conclusion(self):
        self.assertTrue(validar(None))

    def test_extrae_la_celda_del_notebook(self):
        nb = {"cells": [{"cell_type": "markdown", "source": ["## 7 Análisis"]},
                        {"cell_type": "markdown", "source": [texto_valido()]}]}
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "nb.ipynb"
            ruta.write_text(json.dumps(nb), encoding="utf-8")
            self.assertTrue(extraer(ruta).startswith("### Conclusión"))


if __name__ == "__main__":
    unittest.main()
