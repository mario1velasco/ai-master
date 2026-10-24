# Paso 2 · TODO 4 · `hit_pagina`

> Implementa la métrica de localización Hit@k por página.

## Qué hemos hecho

`hit_pagina(paginas_recuperadas, paginas_referencia)` devuelve **1** si hay intersección, **0** si no y **`None`** si la consulta no tiene páginas de referencia (Q5 y Q6). Es una señal de **localización de evidencia, no una prueba de que la respuesta sea correcta**.

## Cómo ejecutarlo

```bash
practica/verificar.sh 2
```

## En qué clase nos fijamos

- [Sesión 6 · §5 Las métricas de recuperación (Precision, Recall@k, MRR…: funciones puras que comparan lo recuperado con los juicios)](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)
- [Sesión 2 · §13 Cómo medir quién gana de verdad: Recall@k](../../clases/02-sistemas-recuper-info/EXPLICACION_sesion_02.md)
- [Código de referencia: `clases/06-Const-evaluacion/src/retrieval_lab/evaluation/metrics.py`](../../clases/06-Const-evaluacion/src/retrieval_lab/evaluation/metrics.py)

## Celda(s) del notebook rellenadas

Celda `hit_pagina` (`d068f253`) → **TODO 4**.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

17 tests OK (pasos 0–2), incluido el cruce con `preguntas.csv` (Q1–Q4 → 1/0, Q5–Q6 → `None`).

## Commit sugerido

- **Mensaje:** `Implementa hit_pagina (TODO 4) con tests`
- **Ficheros:** `practica/tests/test_paso_02_hit_pagina.py`, `practica/Recursos /rag_tenerife.ipynb`
