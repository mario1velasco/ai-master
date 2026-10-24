"""Paso 0 · Entorno: PDF en data/, .env de la práctica (solo nombres) e imports."""
import importlib
import unittest
from dotenv import dotenv_values

from tests.ayudas import PDF, RECURSOS, NOTEBOOK


class Paso00Entorno(unittest.TestCase):
    def test_pdf_en_data(self):
        self.assertTrue(PDF.is_file(), f"Falta {PDF}: cópialo desde 'Recursos /TENERIFE.pdf'")

    def test_recursos_entregables_existen(self):
        for nombre in ("rag_tenerife.ipynb", "utilidades.py", "preguntas.csv", "README.md", "requirements.txt"):
            self.assertTrue((RECURSOS / nombre).is_file(), nombre)

    def test_imports_necesarios(self):
        for modulo in ("langchain_core", "langchain_openai", "langchain_text_splitters", "pypdf", "dotenv", "nbformat"):
            importlib.import_module(modulo)

    def test_env_de_la_practica_define_variables(self):
        env = RECURSOS / ".env"
        if not env.is_file():
            self.skipTest("No hay .env local (no se versiona): créalo según practica/README.md")
        valores = dotenv_values(env)                       # solo se comprueban NOMBRES y si están rellenas
        self.assertTrue(valores.get("OPENAI_API_KEY"), "OPENAI_API_KEY vacía")
        self.assertEqual(valores.get("OPENAI_CHAT_MODEL"), "gpt-5-nano", "El sandbox de EBIS exige gpt-5-nano")

    def test_notebook_es_valido(self):
        import nbformat
        nbformat.validate(nbformat.read(NOTEBOOK, as_version=4))


if __name__ == "__main__":
    unittest.main()
