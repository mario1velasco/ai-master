"""Paso 11 · Empaquetado del ZIP de entrega (sobre una carpeta temporal, nunca sobre la real)."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.empaquetar import OBLIGATORIOS, comprobar, crear_zip


def carpeta_de_entrega(destino, con_clave=False):
    for n in OBLIGATORIOS:
        (destino / n).write_text("sk-" + "a" * 30 if (con_clave and n == "README.md") else "contenido", encoding="utf-8")
    (destino / ".env").write_text("OPENAI_API_KEY=secreta", encoding="utf-8")
    (destino / "data").mkdir()
    (destino / "data" / "TENERIFE.pdf").write_bytes(b"%PDF")
    (destino / "__pycache__").mkdir()


class Paso11Entrega(unittest.TestCase):
    def test_zip_solo_con_lo_exigido(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            carpeta_de_entrega(d)
            zip_ = crear_zip(d, d / "Apellidos_Nombre_RAG_Tenerife.zip")
            nombres = set(zipfile.ZipFile(zip_).namelist())
            self.assertEqual(nombres, set(OBLIGATORIOS))
            for prohibido in (".env", "data/TENERIFE.pdf", "__pycache__"):
                self.assertNotIn(prohibido, nombres)

    def test_falta_un_archivo(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            carpeta_de_entrega(d)
            (d / "revision.csv").unlink()
            self.assertTrue(any("revision.csv" in p for p in comprobar(d)))
            with self.assertRaises(ValueError):
                crear_zip(d, d / "x.zip")

    def test_detecta_claves_de_api(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            carpeta_de_entrega(d, con_clave=True)
            self.assertTrue(any("clave" in p for p in comprobar(d)))

    def test_el_notebook_real_no_contiene_claves(self):
        from tests.ayudas import NOTEBOOK
        self.assertNotIn("sk-", NOTEBOOK.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
