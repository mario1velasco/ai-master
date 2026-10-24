"""Paso 2 · TODO 4 hit_pagina (celda `hit_pagina` del notebook)."""
import unittest

from tests.ayudas import cargar_funciones, RECURSOS
from utilidades import leer_preguntas


class Paso02HitPagina(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hit = staticmethod(cargar_funciones("hit_pagina")["hit_pagina"])

    def test_acierto_por_interseccion(self):
        self.assertEqual(self.hit([3, 5, 9], [5]), 1)

    def test_fallo_sin_interseccion(self):
        self.assertEqual(self.hit([1, 2], [5]), 0)

    def test_no_aplica_sin_referencia(self):
        self.assertIsNone(self.hit([1, 2], []))

    def test_varias_referencias_y_repetidas(self):
        self.assertEqual(self.hit([7, 7, 8], [8, 9]), 1)

    def test_recuperadas_vacias_es_fallo(self):
        self.assertEqual(self.hit([], [5]), 0)

    def test_devuelve_int_o_none(self):
        self.assertIs(type(self.hit([5], [5])), int)

    def test_con_preguntas_csv(self):
        casos = {c["id"]: c["paginas_referencia"] for c in leer_preguntas(RECURSOS / "preguntas.csv")}
        for id_ in ("Q1", "Q2", "Q3", "Q4"):
            self.assertEqual(self.hit(casos[id_], casos[id_]), 1)
        for id_ in ("Q5", "Q6"):
            self.assertIsNone(self.hit([1, 2, 3], casos[id_]))


if __name__ == "__main__":
    unittest.main()
