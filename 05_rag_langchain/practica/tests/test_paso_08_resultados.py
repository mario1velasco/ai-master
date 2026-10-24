"""Paso 8 · validar_resultados sobre una ejecución simulada (sin red)."""
import json
import unittest
from pathlib import Path

from herramientas.validar_resultados import validar
from tests.simulacion import simular


class Paso08Resultados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = simular()
        cls.ruta = Path(cls.tmp.name) / "resultados.json"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_ejecucion_correcta_no_tiene_errores(self):
        self.assertEqual(validar(self.ruta)["errores"], [])

    def test_avisa_de_abstencion_dudosa_en_q5_q6(self):
        avisos = " ".join(validar(self.ruta)["avisos"])
        self.assertIn("Q5", avisos)
        self.assertIn("Q6", avisos)

    def test_detecta_error_tecnico(self):
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        datos[0]["error_tecnico"] = "RateLimitError"
        malo = Path(self.tmp.name) / "malo.json"
        malo.write_text(json.dumps(datos), encoding="utf-8")
        self.assertTrue(any("error técnico" in e for e in validar(malo)["errores"]))

    def test_detecta_menos_de_12(self):
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))[:11]
        corto = Path(self.tmp.name) / "corto.json"
        corto.write_text(json.dumps(datos), encoding="utf-8")
        self.assertTrue(validar(corto)["errores"])

    def test_detecta_hit_pagina_incoherente(self):
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        q5 = next(r for r in datos if r["id"] == "Q5")
        q5["hit_pagina"] = 1
        malo = Path(self.tmp.name) / "hit.json"
        malo.write_text(json.dumps(datos), encoding="utf-8")
        self.assertTrue(any("None" in e for e in validar(malo)["errores"]))


class Paso08AbstencionReconocida(unittest.TestCase):
    def test_respuesta_de_abstencion_no_genera_aviso(self):
        tmp = simular(["La guía no contiene ese dato. No puedo responder."])
        try:
            avisos = validar(Path(tmp.name) / "resultados.json")["avisos"]
            self.assertFalse(any(a.startswith(("Q5", "Q6")) and "abstención" in a for a in avisos))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
