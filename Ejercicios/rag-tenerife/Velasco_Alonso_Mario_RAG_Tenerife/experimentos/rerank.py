"""Retrieve-then-rerank: recuperar k candidatos con el índice y reordenarlos con un cross-encoder.

Reutiliza chunks.py sin modificarlo. Solo mide recuperación (no llama al LLM).
"""
from sentence_transformers import CrossEncoder

from experimentos import chunks

MODELO_RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def cargar_reranker(nombre=MODELO_RERANKER):
    return CrossEncoder(nombre)


def rerank(reranker, pregunta, candidatos):
    """candidatos: Documents del índice (con metadata['score']). Devuelve filas reordenadas."""
    resultado = [{"posición_inicial": i, "chunk_id": d.metadata["chunk_id"],
                  "page": d.metadata["page"], "score_vector": d.metadata["score"],
                  "texto": d.page_content, "doc": d}
                 for i, d in enumerate(candidatos, start=1)]
    pares = [(pregunta, fila["texto"]) for fila in resultado]
    for fila, score in zip(resultado, reranker.predict(pares)):
        fila["score_reranker"] = float(score)
    resultado.sort(key=lambda f: f["score_reranker"], reverse=True)
    for i, fila in enumerate(resultado, start=1):
        fila["posición_reranker"] = i
    return resultado


def imprimir_rerank(pregunta, filas, top_n, recorte=70):
    """Tabla: cómo se mueve cada candidato al reordenar."""
    print(f"\n{pregunta}")
    print(f"{'rerank':>6} {'inicial':>7} {'chunk':>7} {'pág':>4} {'s_vector':>8} "
          f"{'s_rerank':>8}  texto")
    for f in filas:
        texto = " ".join(f["texto"].split())[:recorte]
        marca = " ◀" if f["posición_reranker"] <= top_n else ""
        print(f"{f['posición_reranker']:>6} {f['posición_inicial']:>7} {f['chunk_id']:>7} "
              f"{f['page']:>4} {f['score_vector']:>8.2f} {f['score_reranker']:>8.2f}  "
              f"{texto}{marca}")


def comparar(paginas, fragmentar, preguntas, hit_pagina, local=True, tamaño=500,
             solapamiento=150, k_candidatos=20, top_n=2, detalle=True):
    """Compara top_n sin rerank (orden del índice) frente a top_n tras el cross-encoder."""
    embeddings, _ = chunks.crear_modelos(local)
    fragmentos, indice = chunks.crear_indice(paginas, fragmentar, embeddings,
                                             tamaño, solapamiento)
    k_candidatos = min(k_candidatos, len(fragmentos))
    reranker = cargar_reranker()
    print(f"{tamaño}/{solapamiento}: {len(fragmentos)} fragmentos, "
          f"{k_candidatos} candidatos → top {top_n}")

    filas = []
    for caso in preguntas:
        candidatos = chunks.recuperar_con_score(indice, caso["pregunta"], k_candidatos)
        reordenados = rerank(reranker, caso["pregunta"], candidatos)
        assert {d.metadata["chunk_id"] for d in candidatos} == \
               {f["chunk_id"] for f in reordenados}
        if detalle:
            imprimir_rerank(caso["pregunta"], reordenados, top_n)
        claves = chunks.EVIDENCIAS.get(caso["id"])
        for metodo, docs in (("vector", candidatos[:top_n]),
                             ("rerank", [f["doc"] for f in reordenados[:top_n]])):
            paginas_rec = [d.metadata["page"] for d in docs]
            filas.append({
                "id": caso["id"], "método": metodo,
                "páginas": " ".join(map(str, paginas_rec)),
                "hit": hit_pagina(paginas_rec, caso["paginas_referencia"]),
                "evidencia": None if claves is None else int(chunks.evidencia_en(docs, claves)),
                "chars ctx": sum(len(d.page_content) for d in docs),
            })
    print()
    chunks.imprimir_tabla(filas)
    print()
    resumen = []
    for metodo in ("vector", "rerank"):
        fs = [f for f in filas if f["método"] == metodo]
        resumen.append({
            "método": metodo, "top_n": top_n,
            "hit@n": chunks._media([f["hit"] for f in fs]),
            "evidencia": chunks._media([f["evidencia"] for f in fs]),
            "chars ctx": chunks._media([f["chars ctx"] for f in fs]),
        })
    chunks.imprimir_tabla(resumen)
    return filas, resumen
