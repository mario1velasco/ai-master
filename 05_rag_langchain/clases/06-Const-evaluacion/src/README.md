# Arquitectura del laboratorio

El paquete se organiza en subpaquetes por responsabilidad. Su raíz solo contiene
`__init__.py`; los módulos planos se han trasladado, no duplicado.

```text
src/retrieval_lab/
├── configuration/     settings.py, environment.py
├── data/              corpus.py
├── representations/   providers.py, cache.py, vectors.py, bm25.py
├── storage/           pinecone.py
├── retrieval/         lab.py, preparation.py, engine.py
├── evaluation/        design.py, metrics.py, statistics.py, runner.py, selection.py
├── reporting/         views.py
└── infrastructure/    artifacts.py, concurrency.py, rate_limits.py
```

Todos los subpaquetes incluyen `__init__.py`.

## Cohesión y límites

| Subpaquete | Responsabilidad | Qué queda fuera |
| --- | --- | --- |
| `configuration` | Modelos, parámetros, validación y carga explícita del entorno. | Recuperación y evaluación. |
| `data` | Lectura y validación de TREC-COVID y preparación común del texto. | Embeddings y clientes externos. |
| `representations` | Adaptadores de embeddings, caché reanudable, truncamiento/normalización y codificación BM25. | Consultas Pinecone y métricas de relevancia. |
| `storage` | Índices, namespaces, subidas, verificación, inventario y consultas Pinecone. | Elección de estrategias y evaluación. |
| `retrieval` | Preparación remota; recuperación léxica, densa e híbrida; fusión RRF. | Métricas y selección del ganador. |
| `evaluation` | Diseño experimental, particiones, métricas, bootstrap, ejecución y decisión final. | Visualización y adaptación de proveedores. |
| `reporting` | Tablas, gráficos, ejemplos y presentación de conclusiones. | Algoritmos de recuperación y reglas de decisión. |
| `infrastructure` | Persistencia, firmas, concurrencia, cancelación, cuotas y reintentos. | Decisiones del experimento. |

La agrupación responde al dominio, no al tipo de archivo. Dentro de cada grupo
se mantienen separados los motivos de cambio: `evaluation/metrics.py` define
las fórmulas, `runner.py` ejecuta y agrega mediciones, y `selection.py` aplica
los criterios de elección y congela la decisión.

`retrieval/lab.py` conserva la interfaz docente y el estado compartido; delega
en `preparation.py` y `engine.py`. Los módulos de métricas, estadística,
ejecución y selección no dependen de Jupyter ni de matplotlib.

## Compatibilidad

El notebook de `Notebooks/` conserva las celdas, salidas y metadatos del original;
solo cambia la celda de importaciones. Por ese requisito de copia idéntica, sus
menciones históricas a scripts antiguos en Markdown también se conservan.
La arquitectura vigente es la descrita aquí.

El paquete no importa los scripts originales de la raíz. Se conservan como
versión anterior y referencia para las pruebas de equivalencia.

El arranque añade `src` a la ruta de importación y establece la raíz como
directorio de trabajo. Conserva las rutas de `.env`, `data/` y
`artifacts/pinecone_v1/`. Reorganizar los módulos no cambia las fórmulas,
firmas de caché ni namespaces.

No ejecutes las dos versiones simultáneamente sobre los mismos artefactos.
Reutilizar caché no elimina las comprobaciones remotas, las pequeñas llamadas
de prevalidación ni los embeddings en vivo de la evaluación final.

Consulta [el README principal](../README.md) para instalación y entrega al alumnado.
