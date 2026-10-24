"""Genera resultados.json y revision.csv SIMULADOS (LLM y embeddings falsos) en un directorio temporal."""
import tempfile
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.vectorstores import InMemoryVectorStore

from tests.ayudas import PDF, RECURSOS, cargar_funciones
from utilidades import cargar_paginas, leer_preguntas, ejecutar_pruebas


def simular(respuestas=None):
    e = cargar_funciones("fragmentar", "recuperar", "crear_prompt", "hit_pagina")
    paginas, _ = cargar_paginas(PDF)
    indice = InMemoryVectorStore(embedding=DeterministicFakeEmbedding(size=64))
    indice.add_documents(e["fragmentar"](paginas, 900, 150))
    tmp = tempfile.TemporaryDirectory()
    modelo = FakeListChatModel(responses=respuestas or ["Según la guía, lo indica [TENERIFE.pdf, p. 5]."])
    ejecutar_pruebas(indice, modelo, e["crear_prompt"](), leer_preguntas(RECURSOS / "preguntas.csv"),
                     e["recuperar"], e["hit_pagina"], salida=Path(tmp.name))
    return tmp
