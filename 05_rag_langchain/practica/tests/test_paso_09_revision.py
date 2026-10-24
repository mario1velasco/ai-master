"""Paso 9 · Ayuda de revisión y validación de revision.csv (la revisión es manual; aquí solo la estructura)."""
import csv
import unittest
from pathlib import Path

from herramientas.preparar_revision import bloques, validar_revision, ESPERADAS
from tests.simulacion import simular


def rellenar(ruta, valor_respondible="1", valor_abstencion="1"):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    for r in filas:
        if r["tipo"] == "respondible":
            r["respaldo"] = r["citas"] = valor_respondible
        else:
            r["abstencion"] = valor_abstencion
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader()
        w.writerows(filas)


class Paso09Revision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = simular()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_doce_bloques_con_pregunta_esperado_y_respuesta(self):
        b = bloques(self.dir / "resultados.json")
        self.assertEqual(len(b), 12)
        for texto in b:
            for clave in ("Pregunta:", "Esperado:", "Respuesta del modelo:", "Fragmentos:"):
                self.assertIn(clave, texto)

    def test_hay_respuesta_esperada_para_las_seis_preguntas(self):
        self.assertEqual(set(ESPERADAS), {f"Q{i}" for i in range(1, 7)})

    def test_revision_recien_creada_esta_pendiente(self):
        problemas = validar_revision(self.dir / "revision.csv")
        self.assertTrue(problemas)
        self.assertTrue(all("vacío" in p or "pendiente" in p for p in problemas))

    def test_revision_completa_es_valida(self):
        ruta = self.dir / "completa.csv"
        ruta.write_bytes((self.dir / "revision.csv").read_bytes())
        rellenar(ruta)
        self.assertEqual(validar_revision(ruta), [])

    def test_valores_fuera_de_rango_se_detectan(self):
        ruta = self.dir / "mala.csv"
        ruta.write_bytes((self.dir / "revision.csv").read_bytes())
        rellenar(ruta, valor_respondible="2")
        self.assertTrue(any("0 o 1" in p for p in validar_revision(ruta)))

    def test_resumen_revision_de_utilidades_funciona_con_revision_completa(self):
        import contextlib, io
        from utilidades import resumen_revision
        ruta = self.dir / "completa2.csv"
        ruta.write_bytes((self.dir / "revision.csv").read_bytes())
        rellenar(ruta)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            resumen_revision(ruta)
        self.assertNotIn("pendiente", salida.getvalue())
        self.assertIn("k = 2", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
