# Paso 6 · Modelos (`gpt-5-nano`)

> Adapta la celda de modelos al sandbox de EBIS y prevé la alternativa local de embeddings.

## Qué hemos hecho

- **Chat `gpt-5-nano`** (obligatorio): es un modelo de razonamiento y **no admite `temperature=0`**; se construye sin `temperature` y con `reasoning_effort="low"`, `timeout=60`, `max_retries=1`.
- **Embeddings**: `text-embedding-3-small` (OpenAI) por defecto; `EMBEDDING_PROVIDER=local` usa `paraphrase-multilingual-MiniLM-L12-v2` (sin coste).
- Una celda markdown documenta el cambio y su efecto (respuestas no deterministas).

## Cómo ejecutarlo

```bash
practica/verificar.sh 6          # offline: construye los objetos con una clave falsa
```
**Prueba en vivo (opcional, céntimos)** — ¿la clave EBIS permite embeddings? Solo si lo decides:
```bash
scripts/practica.sh   # y en una celda nueva: embeddings.embed_query('hola'); modelo.invoke('Di hola en una palabra')
```
Si `embed_query` da un error de permisos/modelo, pon `EMBEDDING_PROVIDER=local` en `Recursos /.env`.

## En qué clase nos fijamos

- [Sesión 2 · §11 Probando embeddings de verdad con LangChain (interfaz `Embeddings`, cambiar de proveedor)](../../clases/02-sistemas-recuper-info/EXPLICACION_sesion_02.md)
- [Sesión 7 · §1 De recuperar a responder (dos modelos: embeddings y LLM)](../../clases/07-RAG/EXPLICACION_sesion_07.md)

## Celda(s) del notebook rellenadas

Celda `api_setup` (`15a38d65`) + **nueva celda markdown** «Modelos utilizados y ajustes» tras la introducción de la sección 4.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

55 tests OK (pasos 0–7). Con `gpt-5-nano`: `temperature` es `None` y `reasoning_effort == 'low'`.

## Commit sugerido

- **Mensaje:** `Adapta la celda de modelos a gpt-5-nano y prevé embeddings locales`
- **Ficheros:** `practica/tests/test_paso_06_modelos.py`, `practica/Recursos /rag_tenerife.ipynb`
