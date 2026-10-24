"""Paso 6 · Celda `api_setup`: gpt-5-nano sin temperature, proveedor de embeddings. Sin red."""
import os
import unittest
from unittest import mock

from tests.ayudas import cargar_funciones, celda_por_etiqueta, fuente


def ejecutar_celda(entorno):
    espacio = cargar_funciones()               # imports del notebook
    espacio["load_dotenv"] = lambda *a, **k: False   # no leer el .env real: el test controla el entorno
    base = {"OPENAI_API_KEY": "clave-de-prueba", "OPENAI_CHAT_MODEL": "gpt-5-nano",
            "EMBEDDING_PROVIDER": "openai", "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small"}
    with mock.patch.dict(os.environ, {**base, **entorno}, clear=False):
        exec(compile(fuente(celda_por_etiqueta("api_setup")), "<api_setup>", "exec"), espacio)
    return espacio


class Paso06Modelos(unittest.TestCase):
    def test_gpt5_nano_sin_temperature_y_con_razonamiento_bajo(self):
        e = ejecutar_celda({})
        self.assertEqual(e["CHAT_MODEL"], "gpt-5-nano")
        self.assertIsNone(e["modelo"].temperature)
        self.assertEqual(e["modelo"].reasoning_effort, "low")
        self.assertEqual(e["modelo"].request_timeout, 60)
        self.assertEqual(e["modelo"].max_retries, 1)

    def test_modelos_no_gpt5_mantienen_temperature_cero(self):
        e = ejecutar_celda({"OPENAI_CHAT_MODEL": "gpt-4.1-mini"})
        self.assertEqual(e["modelo"].temperature, 0)

    def test_embeddings_openai_por_defecto(self):
        e = ejecutar_celda({})
        self.assertEqual(type(e["embeddings"]).__name__, "OpenAIEmbeddings")
        self.assertEqual(e["EMBEDDING_MODEL"], "text-embedding-3-small")

    def test_alternativa_local_esta_prevista(self):
        codigo = fuente(celda_por_etiqueta("api_setup"))
        self.assertIn("HuggingFaceEmbeddings", codigo)
        self.assertIn('EMBEDDING_PROVIDER == "local"', codigo)

    def test_sin_clave_falla_con_mensaje_claro(self):
        espacio = cargar_funciones()
        espacio["load_dotenv"] = lambda *a, **k: False
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                exec(compile(fuente(celda_por_etiqueta("api_setup")), "<api_setup>", "exec"), espacio)

    def test_la_clave_no_esta_escrita_en_el_notebook(self):
        from tests.ayudas import NOTEBOOK
        self.assertNotIn("sk-", NOTEBOOK.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
