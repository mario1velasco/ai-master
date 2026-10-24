# Sesión 07 · UMBRA: recuperación y generación con evidencia

Continuación de Sesión 06. Punto de entrada: **`Notebooks/01_retrieval_y_rag.ipynb`**.
Contiene el recorrido previo como referencia y la extensión RAG. La aplicación usa
el mismo motor Python, no una segunda implementación escondida.

## Qué incluye

- RAG estándar: pregunta literal → embedding → híbrido → contexto → LLM con citas.
- RAG con herramienta: el LLM propone la consulta; Python valida y ejecuta la búsqueda.
- Comparación exploratoria de llamadas, tokens, fuentes y latencia, más revisión humana.
- Extras ejecutables acotados inspirados en GraphRAG y RAPTOR, con sus simplificaciones explícitas.
- UMBRA: catálogo real, conversación, dos modos, fuentes consultables y trazas.

La configuración recuperada del cierre de Sesión 06 es OpenAI, 256 dimensiones,
búsqueda híbrida y 100 candidatos por rama. El informe no confirmó una mejora
estadísticamente concluyente frente a la referencia; aquí reutilizamos el candidato
elegido, sin elevar esa selección a garantía universal.

## Entorno

Python 3.11 o 3.12 y Node.js 20.19+ o 22.12+ para compilar la interfaz.
Desde esta carpeta:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name umbra-rag --display-name "Python (umbra-rag)"
jupyter lab
```

En Windows, activa con `.venv\Scripts\Activate.ps1`. Selecciona el kernel
**Python (umbra-rag)**. No modifiques el entorno de Sesión 06 para esta continuación.

`RUN_LIVE = False` permite recorrer el cuaderno sin llamadas a proveedores.
Al cambiarlo a `True`, se ejecutan búsquedas y generación reales. `REPLAY_SESSION06`
permanece desactivado para no repetir la preparación/benchmark anterior.
`RUN_EXTRAS` activa el gasto adicional de extracción y resúmenes; no lo actives
hasta terminar los dos enfoques principales. No se han ejecutado llamadas pagadas
para construir o verificar el material.

## Reutilizar Sesión 06

La carpeta se busca al mismo nivel, tanto con acentos Unicode compuestos como
descompuestos. Si está en otra ubicación, define `SESSION06_DIR` en el entorno
o en un `.env` de Sesión 07. La ruta puede ser absoluta o relativa a esta carpeta.

Se leen, sin modificar:

- `.env` de Sesión 06: las claves no se copian ni se envían al navegador.
- `data/trec-covid/corpus.jsonl`: textos originales.
- `artifacts/pinecone_v1/results/frozen_decision.json`: modelo, dimensión y namespaces.
- `artifacts/pinecone_v1/indexes/bm25-*/ready.json` y `vocabulary.json`: codificación léxica idéntica.

El orden de configuración es entorno del proceso, `.env` de Sesión 07 y `.env`
de Sesión 06. Solo se heredan valores no vacíos. `.env.example` no contiene secretos.
El modelo generativo se elige en `config/rag.yaml` o con `RAG_LLM_MODEL`.

**El adaptador RAG es de solo lectura en Pinecone.** No descarga embeddings del
corpus, no crea índices, no hace upsert y no ajusta BM25. No precisa cargar la
matriz BM25 completa: la consulta usa el vocabulario ya aprendido. Los índices
deben seguir existiendo en el proyecto asociado a la clave. Una carpeta de caché
local no sustituye a los vectores remotos.

Las preguntas nuevas sí producen embeddings de consulta. La caché de respuestas
de Sesión 07 evita repetir una petición idéntica con igual configuración e historial;
no es una caché global de búsquedas ni reutiliza una pregunta parecida. Sus archivos
se guardan en `artifacts/rag/answers/`. Contienen preguntas, respuestas y pasajes:
no los publiques sin revisar privacidad. Puedes desactivarla con `answer_cache: false`.

## Arrancar la aplicación

Compila desde `app/`:

```bash
npm install
npm run build
```

Vuelve a la raíz de Sesión 07 y arranca el servidor:

```bash
python -m uvicorn umbra.api.server:app --host 127.0.0.1 --port 8007
```

Abre **http://127.0.0.1:8007**. El servidor sirve la interfaz compilada y la API.
Para desarrollar: arranca Python en 8007 y `npm run dev` en `app/`; abre
http://127.0.0.1:5173. Vite redirige `/api` al backend.

El catálogo realiza búsqueda literal local sobre los artículos, sin consumo API.
Los temas proponen términos ingleses. El librero llama servicios reales: un fallo
se muestra como fallo, nunca se reemplaza por una respuesta inventada. Las fuentes
abren el texto de TREC-COVID; la búsqueda externa por título no afirma disponer de DOI.
La conversación se mantiene en memoria del navegador, no en una base de usuarios.

## Límites y seguridad

- 100 candidatos por rama; hasta seis documentos y 6.500 tokens de fuentes por búsqueda.
- Hasta dos llamadas a la herramienta; la segunda puede aportar seis fuentes distintas.
  El máximo de fuentes/contexto acumulado es, por tanto, mayor que en RAG estándar.
- Máximo 2.000 caracteres por pregunta, ocho mensajes de historial y una solicitud
  de chat activa por proceso. Los SDK usan tiempos de espera y reintentos acotados.
- Las etiquetas de cita se comprueban, pero su existencia no prueba fidelidad factual.
  Lee los pasajes: no hay un juez automático de veracidad.
- Los documentos se tratan como datos no confiables. Esto reduce riesgo de inyección,
  no demuestra inmunidad. La única herramienta permitida es búsqueda de solo lectura.
- TREC-COVID es histórico. La app no es un dispositivo de asesoramiento médico.
- El servidor es una aplicación docente local, **no un servicio público listo para desplegar**.
  Exponerlo necesita autenticación, autorización, límites por usuario, control de gasto,
  protección de datos, observabilidad y revisión de seguridad.
- `store=False` evita guardar objetos Responses por esa opción de la API; no equivale
  a una promesa de retención cero del proveedor. Las preguntas y fuentes sí se envían al LLM.

## Organización

```text
Notebooks/           referencia y continuación docente
config/              límites y modelo generativo
src/umbra/
  configuration/     rutas, entorno y parámetros
  data/              corpus y catálogo
  domain/            contratos de evidencia, búsqueda y respuesta
  retrieval/         decisión heredada y búsqueda híbrida de solo lectura
  generation/        prompts, contexto, proveedor, flujos y caché de respuestas
  evaluation/        comparación exploratoria de enfoques
  experiments/       grafo local y jerarquía de resúmenes opcionales
  presentation/      presentación en el notebook
  api/               interfaz HTTP local
src/retrieval_lab/   copia del código de Sesión 06 para la referencia y utilidades
app/                 frontend React + Vite, componentes y activos
tests/               pruebas sin consumo API
design/              concepto visual y especificación
```

## Entrega y pruebas

Entrega esta carpeta sin `.env`, `.venv`, `node_modules`, `__pycache__` ni artefactos
privados. Conserva el archivo de bloqueo de npm, `app/public`, `src`, `config`,
requisitos y notebook. Para funcionar, cada alumno necesita además la selección,
el corpus, el vocabulario BM25 de Sesión 06 y acceso a sus índices Pinecone.
No compartas tu clave personal. Revisa las condiciones de redistribución del dataset.

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Las pruebas simulan LLM y Pinecone. No producen métricas reales del caso de uso.
El notebook deja explícito qué puede comprobarse localmente y qué exige `RUN_LIVE`.

Referencias: [Function calling](https://developers.openai.com/api/docs/guides/function-calling),
[GraphRAG](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/),
[RAPTOR](https://arxiv.org/abs/2401.18059).
