# Paso 7 · Índice

> Construye el índice en memoria una sola vez y comprueba que tiene todos los fragmentos.

## Qué hemos hecho

La celda ya suministrada fragmenta y crea `InMemoryVectorStore`. No necesita cambios de código: se **verifica** con embeddings falsos que hay un vector por fragmento (33) y que `add_documents` se llama **una sola vez** (el mismo índice sirve para `k=2` y `k=4`).

## Cómo ejecutarlo

```bash
practica/verificar.sh 7
```
**En vivo (opcional, ~33 embeddings, céntimos):** ejecutar la celda `index` en el notebook.

## En qué clase nos fijamos

- [Sesión 4 · §8 Baseline exacto (`IndexFlatIP`): búsqueda exhaustiva como referencia](../../clases/04-indexacion-busq-efic/EXPLICACION_sesion_04.md)
- [Sesión 5 · §6 Conectar e ingerir (IDs estables, ingesta idempotente)](../../clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md)

## Celda(s) del notebook rellenadas

Celda `index` (`85246d20`): sin cambios de código; se ejecuta en vivo.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

Tests OK: `len(indice.store) == len(fragmentos) == 33`.

## Commit sugerido

- **Mensaje:** `Verifica la construcción del índice con embeddings falsos`
- **Ficheros:** `practica/tests/test_paso_07_indice.py`
