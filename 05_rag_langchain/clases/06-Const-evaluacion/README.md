# Evaluación offline de recuperación en Pinecone

Abre **`Notebooks/01_retrieval_system_evaluation.ipynb`**. El código está en
subpaquetes dentro de `src/retrieval_lab/`; consulta
[la arquitectura y sus responsabilidades](src/README.md).

El ejercicio utiliza TREC-COVID, BM25, embeddings de OpenAI y recuperación
densa e híbrida en Pinecone. Qwen es opcional. Google no está activo por defecto
y no se necesita una clave de Google para este recorrido.

“Offline” significa evaluar con consultas y juicios conocidos: **requiere
Internet y servicios externos**. No es un A/B con tráfico real de usuarios.

## Preparar el entorno

Usa Python 3.11 o 3.12 para este material. Desde la raíz de la carpeta entregada:

```bash
python -m venv .venv
```

Activa el entorno en macOS/Linux:

```bash
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instala las dependencias y registra el kernel:

```bash
python -m pip install -r requirements.txt
python -m ipykernel install --user --name retrieval-system --display-name "Python (retrieval-system)"
jupyter lab
```

Abre el notebook de `Notebooks/` y selecciona **Python (retrieval-system)**.
También puedes abrir la carpeta raíz en VSCode y seleccionar ese kernel.
Si ya tienes el entorno preparado, reutilízalo: la reorganización no añade dependencias.

Los requisitos conservan dependencias opcionales de modelos locales y del
adaptador de Google. Instalarlas no activa esos modelos ni realiza inferencia.

## Credenciales y recursos

Copia `.env.example` como `.env` en la raíz y completa localmente:

- `OPENAI_API_KEY`.
- `PINECONE_API_KEY`.

Configura también prefijo de índices, nube y región. Usa un prefijo propio por
alumno si compartís proyecto Pinecone. `OPENAI_EMBEDDING_RPM` y
`OPENAI_EMBEDDING_TPM` permiten acotar las llamadas según la cuota disponible;
vacíos significan que no se fija un límite local.

No compartas `.env` ni claves reales. Necesitas capacidad y permisos en los
servicios. Preparar el corpus completo puede superar cuotas gratuitas y genera
costes reales. Revisa el volumen mostrado antes de ejecutar todas las celdas.

## Qué se compara

Por defecto: OpenAI con 256, 512 y 768 dimensiones, profundidades de candidatos
20, 50 y 100, estrategias densa e híbrida y una referencia BM25:
**19 configuraciones**. Qwen con esas mismas dimensiones añade 18: **37** en total.
El notebook calcula el número efectivo a partir de la configuración.

El barrido mide búsquedas con embeddings precalculados; la comprobación final
incluye el embedding de consulta en vivo. Se emplean métricas de ranking,
recall normalizado por `min(k, relevantes)`, latencia y comparación pareada.
El ejercicio no modifica parámetros HNSW/IVF/PQ del servicio.

`include_qwen=True` activa inferencia local y puede descargar pesos la primera
vez. Sus salidas configuradas también son 256, 512 y 768; no implica crear
un índice de 1024 dimensiones.

## Caché y reejecución

La primera celda encuentra la raíz al iniciar desde ella o desde `Notebooks/`,
añade `src` a la ruta de importación y establece la raíz como directorio de trabajo.
Se mantienen las rutas:

- `data/trec-covid/`: corpus, consultas y juicios; si falta, se descarga.
- `artifacts/pinecone_v1/embeddings/`: matrices, manifiestos y progreso reanudable.
- `artifacts/pinecone_v1/indexes/`: representación BM25 y marcadores de carga.
- `artifacts/pinecone_v1/results/`: particiones, mediciones y decisión congelada.

La reorganización no invalida la caché. Reutilizarla requiere que coincidan los
textos, IDs, modelo y parámetros relevantes. Conserva las carpetas completas
con sus manifiestos y archivos de progreso, no solo los archivos de vectores.

**Caché no significa cero llamadas:** `prepare_dense()` realiza una prevalidación
pequeña por modelo. Las consultas y verificaciones Pinecone siguen siendo remotas,
y la evaluación final genera embeddings en vivo. En otro proyecto/cuenta Pinecone
habrá que subir los vectores aunque los embeddings estén cacheados localmente.
Los marcadores locales no contienen ni sustituyen los vectores remotos.

No ejecutes simultáneamente la versión antigua y la nueva sobre los mismos
artefactos. El notebook no borra recursos remotos; revisa los índices al terminar.

## Qué entregar a los alumnos

Prepara una carpeta nueva con esta estructura mínima, conservando las rutas:

```text
laboratorio/
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── README.md
│   └── retrieval_lab/                 # Todos los subpaquetes y archivos .py
└── Notebooks/
    └── 01_retrieval_system_evaluation.ipynb
```

No necesitan los scripts antiguos. Cada alumno crea su `.env`, instala el
entorno y descarga/prepara los datos. **Esta entrega mínima no evita generar
embeddings ni poblar Pinecone.**

Para partir del material ya preparado, añade:

- `data/trec-covid/` completo: `corpus.jsonl`, `queries.jsonl` y `qrels/test.tsv`.
- Las cachés compatibles de `artifacts/pinecone_v1/embeddings/`, tanto de
  documentos como de consultas, con matrices, manifiestos y progreso.
- Las carpetas `bm25-*` completas de `artifacts/pinecone_v1/indexes/`.
  No necesitan tus marcadores `upload-*.json`.

No incluyas por defecto `artifacts/pinecone_v1/results/`: contiene tus resultados
y decisiones congeladas, no la caché de embeddings. Una decisión previa puede
impedir una nueva selección. Entrega resultados de referencia aparte si los necesitas,
fuera del directorio activo de resultados.

Las cachés pueden ser grandes y contienen información del corpus y las consultas;
revísalas antes de distribuirlas y comprueba la licencia del dataset.
Los alumnos siguen necesitando acceso a OpenAI y Pinecone para el recorrido completo.

Revisa también las salidas guardadas del notebook y límpialas en la copia de
entrega si no quieres compartir resultados, identificadores de recursos o mensajes.
La copia de trabajo conserva las salidas originales.

**No entregues:** `.env`, `.venv/`, `__pycache__/`, `.DS_Store`, `.git/`,
`.presentation-build/`, `tmp/`, el resto de `output/`, presentaciones innecesarias,
los scripts Python antiguos ni el notebook antiguo de la raíz.
No comprimas todo el workspace sin seleccionar su contenido.

## Pruebas sin credenciales

Opcionalmente, entrega `tests/test_modular_retrieval.py` y ejecuta:

```bash
python -m unittest discover -s tests -p 'test_modular_retrieval.py' -q
```

Utiliza servicios simulados, sin APIs reales. La prueba con una muestra local
de TREC-COVID se omite si el dataset no está disponible.

En el workspace docente, que conserva los originales, puedes ejecutar además:

```bash
python -m unittest discover -s tests -p 'test_*.py' -q
```

`tests/test_refactor_equivalence.py` necesita los scripts antiguos para comparar
versiones: no forma parte de la entrega mínima al alumnado.
