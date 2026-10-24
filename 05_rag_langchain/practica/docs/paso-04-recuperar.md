# Paso 4 · TODO 2 · `recuperar`

> Crea el retriever con `k` y recupera los fragmentos sin usar las páginas de referencia.

## Qué hemos hecho

`indice.as_retriever(search_kwargs={"k": k}).invoke(pregunta)`, con un `ValueError` si `k < 1`. La firma **no admite** páginas de referencia: la evaluación se hace después.

## Cómo ejecutarlo

```bash
practica/verificar.sh 4
```
Los tests usan `InMemoryVectorStore` con `DeterministicFakeEmbedding`: sin red.

## En qué clase nos fijamos

- [Sesión 4 · §12 Recuperación idiomática con LangChain (`as_retriever`)](../../clases/04-indexacion-busq-efic/EXPLICACION_sesion_04.md)
- [Sesión 4 · §7 Un mismo contrato LangChain para índices distintos](../../clases/04-indexacion-busq-efic/EXPLICACION_sesion_04.md)
- [Sesión 5 · §7 Recuperación semántica con filtros (`similarity_search`)](../../clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md)

## Celda(s) del notebook rellenadas

Celda `recuperar` (`47094d1d`) → **TODO 2**.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

34 tests OK (pasos 0–4): devuelve `k` documentos con metadatos de cita, orden estable y `k=2` = los dos primeros de `k=4`.

## Commit sugerido

- **Mensaje:** `Implementa recuperar (TODO 2) con as_retriever`
- **Ficheros:** `practica/tests/test_paso_04_recuperar.py`, `practica/Recursos /rag_tenerife.ipynb`
