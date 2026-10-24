"""Paso 5 · TODO 3 crear_prompt + simulación completa offline (12 ejecuciones, sin red)."""
import csv
import json
import re
import tempfile
import unittest
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.vectorstores import InMemoryVectorStore

from tests.ayudas import PDF, RECURSOS, cargar_funciones
from utilidades import cargar_paginas, leer_preguntas, ejecutar_pruebas

REGEX_CITA = r"\[TENERIFE\.pdf, p\. (\d+)\]"   # el mismo que usa utilidades.ejecutar_pruebas


class Paso05Prompt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.espacio = cargar_funciones("fragmentar", "recuperar", "crear_prompt", "hit_pagina")
        cls.prompt = cls.espacio["crear_prompt"]()

    def render(self, pregunta="P?", contexto="C"):
        return "\n".join(m.content for m in self.prompt.invoke({"pregunta": pregunta, "contexto": contexto}).messages)

    def test_variables_exactas(self):
        self.assertEqual(set(self.prompt.input_variables), {"pregunta", "contexto"})

    def test_pide_espanol_y_solo_contexto(self):
        texto = self.render().lower()
        self.assertIn("español", texto)
        self.assertIn("únicamente", texto)
        self.assertIn("conocimiento externo", texto)

    def test_formato_de_cita_exacto(self):
        texto = self.render()
        self.assertRegex(texto, REGEX_CITA.replace(r"(\d+)", r"(?:N|\d+)"))
        self.assertIn("[TENERIFE.pdf, p. 15]", texto)

    def test_abstencion_y_limite_documental(self):
        texto = self.render().lower()
        self.assertIn("no contiene", texto)
        self.assertIn("no lo inventes", texto)

    def test_no_convierte_datos_sin_fecha_en_vigentes(self):
        texto = self.render().lower()
        for palabra in ("precios", "horarios", "permisos", "accesos", "sin fecha", "información oficial"):
            self.assertIn(palabra, texto)

    def test_distingue_pdf_de_instrucciones(self):
        texto = self.render().lower()
        self.assertIn("datos", texto)
        self.assertIn("instrucciones", texto)

    def test_la_pregunta_y_el_contexto_llegan_al_prompt(self):
        texto = self.render(pregunta="¿QUÉ-MIRADOR?", contexto="CONTEXTO-PRUEBA")
        self.assertIn("¿QUÉ-MIRADOR?", texto)
        self.assertIn("CONTEXTO-PRUEBA", texto)

    def test_no_hay_llaves_sin_resolver(self):
        self.assertNotRegex(self.render(), r"[{}]")


class Paso05SimulacionOffline(unittest.TestCase):
    """Corre el flujo real de utilidades.ejecutar_pruebas con un LLM y embeddings falsos."""

    @classmethod
    def setUpClass(cls):
        e = cargar_funciones("fragmentar", "recuperar", "crear_prompt", "hit_pagina")
        paginas, _ = cargar_paginas(PDF)
        frags = e["fragmentar"](paginas, 900, 150)
        indice = InMemoryVectorStore(embedding=DeterministicFakeEmbedding(size=64))
        indice.add_documents(frags)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.salida = Path(cls.tmp.name)
        modelo = FakeListChatModel(responses=["Según la guía, respuesta de prueba [TENERIFE.pdf, p. 5]."])
        preguntas = leer_preguntas(RECURSOS / "preguntas.csv")
        cls.resultados = ejecutar_pruebas(indice, modelo, e["crear_prompt"](), preguntas,
                                          e["recuperar"], e["hit_pagina"], salida=cls.salida)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_doce_ejecuciones(self):
        self.assertEqual(len(self.resultados), 12)
        self.assertEqual({(r["id"], r["k"]) for r in self.resultados},
                         {(f"Q{i}", k) for i in range(1, 7) for k in (2, 4)})

    def test_recupera_k_fragmentos_y_sin_errores(self):
        for r in self.resultados:
            self.assertEqual(len(r["fragmentos"]), r["k"])
            self.assertEqual(r["error_tecnico"], "")

    def test_hit_pagina_solo_en_respondibles(self):
        for r in self.resultados:
            if r["tipo"] == "sin_respuesta":
                self.assertIsNone(r["hit_pagina"])
            else:
                self.assertIn(r["hit_pagina"], (0, 1))

    def test_se_extraen_las_paginas_citadas(self):
        self.assertTrue(all(r["paginas_citadas"] == [5] for r in self.resultados))

    def test_resultados_json_y_revision_csv(self):
        datos = json.loads((self.salida / "resultados.json").read_text(encoding="utf-8"))
        self.assertEqual(len(datos), 12)
        with open(self.salida / "revision.csv", encoding="utf-8-sig", newline="") as f:
            filas = list(csv.DictReader(f))
        self.assertEqual(len(filas), 12)
        self.assertEqual({r["k"] for r in filas}, {"2", "4"})


if __name__ == "__main__":
    unittest.main()
