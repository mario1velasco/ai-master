"""Barrido de fragmentación: fragmentar → indexar → recuperar con score → generar → medir.

Las páginas de referencia y EVIDENCIAS solo se usan después de recuperar; nunca
llegan al buscador ni al modelo. No escribe resultados.json ni revision.csv.
"""
import os
import re

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import InMemoryVectorStore

from utilidades import construir_contexto

TAMAÑOS = (300, 500, 700, 900, 1200, 2500)
SOLAPES = (0, 150, 300)
KS = (2, 4, 6)
ACTUAL = (900, 150)

# Frases del PDF que una respuesta correcta necesita juntas (solo para medir).
EVIDENCIAS = {
    "Q1": ["Anaga", "La Jardina", "favorito"],
    "Q2": ["TF24", "La Laguna", "Tarta"],
    "Q3": ["Carajita", "Fogalera", "Reina Pepiada"],
    "Q4": ["Los Cristianos", "Playa de Las Vistas"],
}

ABSTENCION = re.compile(
    r"no (contiene|incluye|especifica|menciona|aparece|dispon|tengo|indica|proporciona)",
    re.IGNORECASE)


def crear_modelos(local):
    """local=True: embeddings locales + Haiku; False: OpenAI de la práctica."""
    load_dotenv()
    temperature = 0
    if local:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_anthropic import ChatAnthropic

        def exigir(variable):
            if not os.environ.get(variable):
                raise RuntimeError(f"Configura {variable} en .env antes de ejecutar.")

        print("Embeddings: modelo local")
        EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},   # modelo pequeño: en CPU evita bloqueos con la GPU
            encode_kwargs={"normalize_embeddings": True},
        )

        print("Chat: Claude (Anthropic)")
        exigir("ANTHROPIC_API_KEY")
        CHAT_MODEL = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-haiku-4-5-20251001")
        modelo = ChatAnthropic(model=CHAT_MODEL, temperature=temperature, timeout=60, max_retries=1)
    else:
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("Configura OPENAI_API_KEY en .env antes de ejecutar.")
        CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-5-nano")
        EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        modelo = ChatOpenAI(model=CHAT_MODEL, temperature=temperature, timeout=60, max_retries=1)
    print({"chat": CHAT_MODEL, "embeddings": EMBEDDING_MODEL, "temperatura": temperature})
    return embeddings, modelo


def crear_indice(paginas, fragmentar, embeddings, tamaño, solapamiento):
    fragmentos = fragmentar(paginas, tamaño, solapamiento)
    assert fragmentos and all("page" in d.metadata for d in fragmentos)
    indice = InMemoryVectorStore(embedding=embeddings)
    indice.add_documents(fragmentos)
    return fragmentos, indice


def recuperar_con_score(indice, pregunta, k):
    """Documents del más al menos similar, con el score en metadata['score']."""
    docs = []
    for doc, score in indice.similarity_search_with_score(pregunta, k=k):
        doc.metadata["score"] = score
        docs.append(doc)
    return docs


def evidencia_en(docs, claves):
    """True si algún fragmento recuperado contiene todas las claves."""
    return any(all(c in re.sub(r"\s+", " ", d.page_content) for c in claves)
               for d in docs)


def ejecutar_pruebas_chunks(indice, modelo, prompt, preguntas, hit_pagina,
                            ks=KS, generar=True):
    cadena = prompt | modelo | StrOutputParser() if generar else None
    registros = []
    for caso in preguntas:
        # Una búsqueda con el k mayor; la búsqueda exacta da el mismo orden al recortar.
        todos = recuperar_con_score(indice, caso["pregunta"], max(ks))
        for k in ks:
            docs = todos[:k]
            respuesta = ""
            error = ""
            if generar:
                try:
                    respuesta = cadena.invoke({"pregunta": caso["pregunta"],
                                               "contexto": construir_contexto(docs)})
                except Exception as exc:
                    # No volcar mensajes del proveedor que puedan incluir credenciales.
                    error = type(exc).__name__
            paginas = [d.metadata["page"] for d in docs]
            citadas = [int(x) for x in re.findall(
                r"\[TENERIFE\.pdf, p\. (\d+)\]", respuesta)]
            claves = EVIDENCIAS.get(caso["id"])
            registros.append({
                "id": caso["id"], "tipo": caso["tipo"], "k": k,
                "pregunta": caso["pregunta"],
                "paginas": paginas,
                "chunks": [d.metadata["chunk_id"] for d in docs],
                "scores": [round(d.metadata["score"], 3) for d in docs],
                "textos": [d.page_content for d in docs],
                "respuesta": respuesta, "error_tecnico": error,
                "hit_pagina": hit_pagina(paginas, caso["paginas_referencia"]),
                "evidencia": None if claves is None else int(evidencia_en(docs, claves)),
                "citas_validas": bool(citadas) and set(citadas).issubset(set(paginas)),
                "abstencion": bool(ABSTENCION.search(respuesta)) and not citadas,
                "chars_contexto": sum(len(d.page_content) for d in docs),
            })
    return registros


def _media(valores):
    valores = [v for v in valores if v is not None]
    return sum(valores) / len(valores) if valores else float("nan")


def resumir(registros, tamaño, solapamiento, n_fragmentos, generar):
    filas = []
    for k in sorted({r["k"] for r in registros}):
        rs = [r for r in registros if r["k"] == k]
        resp = [r for r in rs if r["tipo"] == "respondible"]
        sin = [r for r in rs if r["tipo"] != "respondible"]
        fila = {
            "tamaño": tamaño, "solap": solapamiento, "k": k,
            "nº frag": n_fragmentos,
            "hit@k": _media([r["hit_pagina"] for r in resp]),
            "evidencia": _media([r["evidencia"] for r in resp]),
            "score top1": _media([r["scores"][0] for r in rs if r["scores"]]),
            "chars ctx": _media([r["chars_contexto"] for r in rs]),
        }
        if generar:
            fila["citas"] = _media([int(r["citas_validas"]) for r in resp])
            fila["abstencion"] = _media([int(r["abstencion"]) for r in sin])
            fila["errores"] = sum(bool(r["error_tecnico"]) for r in rs)
        fila["actual"] = "◀" if (tamaño, solapamiento) == ACTUAL else ""
        filas.append(fila)
    return filas


def barrido(paginas, fragmentar, prompt, preguntas, hit_pagina, local=True,
            generar=True, tamaños=TAMAÑOS, solapes=SOLAPES, ks=KS):
    """Devuelve (filas, detalle, indices). filas: una por tamaño/solap/k, ordenadas por tamaño, solap y k."""
    embeddings, modelo = crear_modelos(local)
    filas, detalle, indices = [], {}, {}
    for tamaño in tamaños:
        for solapamiento in solapes:
            if solapamiento >= tamaño:
                continue
            fragmentos, indice = crear_indice(paginas, fragmentar, embeddings,
                                              tamaño, solapamiento)
            indices[(tamaño, solapamiento)] = indice
            registros = ejecutar_pruebas_chunks(indice, modelo, prompt, preguntas,
                                                hit_pagina, ks, generar)
            detalle[(tamaño, solapamiento)] = registros
            filas += resumir(registros, tamaño, solapamiento, len(fragmentos), generar)
            errores = sum(bool(r["error_tecnico"]) for r in registros)
            print(f"tamaño={tamaño:>4} solap={solapamiento:>3}: {len(fragmentos)} fragmentos,"
                  f" {len(registros)} pruebas, errores={errores}")
    filas.sort(key=lambda f: (f["tamaño"], f["solap"], f["k"]))
    return filas, detalle, indices


def imprimir_tabla(filas):
    """Tabla por pantalla, ordenada por tamaño, solapamiento y k."""
    columnas = list(filas[0])
    print("  ".join(f"{c:>10}" for c in columnas))
    for f in filas:
        print("  ".join(f"{f[c]:>10.2f}" if isinstance(f[c], float) else f"{f[c]!s:>10}"
                        for c in columnas))


def imprimir_pivot(filas, metrica="evidencia"):
    """Filas tamaño/solap, columnas k: una métrica de un vistazo."""
    ks = sorted({f["k"] for f in filas})
    celdas = {(f["tamaño"], f["solap"], f["k"]): f[metrica] for f in filas}
    print(f"{metrica:>12} " + " ".join(f"{'k=' + str(k):>6}" for k in ks))
    for t, s in sorted({(f["tamaño"], f["solap"]) for f in filas}):
        print(f"{t:>6}/{s:<5} " + " ".join(f"{celdas[t, s, k]:>6.2f}" for k in ks))
