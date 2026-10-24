# Paso 3 · TODO 1 · `fragmentar`

> Divide el PDF en fragmentos conservando `source`/`page` y añadiendo un `chunk_id` único; justifica 900/150.

## Qué hemos hecho

`RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150).split_documents(paginas)` **por página**, y a cada fragmento se le añade `chunk_id = p{página}-c{n}`. Salen **33 fragmentos** (media ~517 caracteres). Se añade una celda markdown con la justificación del tamaño y el solape. `utilidades.construir_contexto` **necesita `chunk_id`**.

## Cómo ejecutarlo

```bash
practica/verificar.sh 3
```

## En qué clase nos fijamos

- [Sesión 7 · §4 Candidatos y contexto: tres presupuestos distintos (empaquetar el contexto, tamaños)](../../clases/07-RAG/EXPLICACION_sesion_07.md)
- [Sesión 6 · §8 (no cambiar chunking y modelo a la vez; qué se pierde al recortar)](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)
- [Sesión 5 · §2 (unidad recuperable, ID de documento padre en chunks)](../../clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md)

## Celda(s) del notebook rellenadas

Celda `fragmentar` (`11577479`) → **TODO 1**; **nueva celda markdown** de justificación tras la introducción de la sección 2.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

28 tests OK (pasos 0–3): metadatos preservados, `chunk_id` único, ningún fragmento > 900, 33 fragmentos, p.7 ausente.

> **Honestidad**: `RecursiveCharacterTextSplitter` **no se usa en ninguna clase**; procede de `langchain-text-splitters` (ya en el `requirements.txt`).

## Commit sugerido

- **Mensaje:** `Implementa fragmentar (TODO 1) con chunk_id y justifica 900/150`
- **Ficheros:** `practica/tests/test_paso_03_fragmentar.py`, `practica/Recursos /rag_tenerife.ipynb`
