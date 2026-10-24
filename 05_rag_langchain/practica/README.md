# Práctica final · Un asistente turístico con RAG (Tenerife)

Guía paso a paso para terminar la práctica del Tema 5 en **mini-tareas**. Cada paso:
**se ejecuta sin fallos**, **se puede commitear por separado**, tiene su test (`practica/verificar.sh N`) y su
documento en [`docs/`](./docs/) (qué se hizo, cómo ejecutarlo y **en qué clase nos fijamos**).

> Cómo trabaja el asistente en esta carpeta, cómo se testea y dónde mirar en `clases/`: [`Agent.md`](./Agent.md).
> Contexto general del repositorio: [`../CLAUDE.md`](../CLAUDE.md) (sección 6 = enunciado completo).

## 1. Qué hay que entregar

Un ZIP `Apellidos_Nombre_RAG_Tenerife.zip` con:

| Archivo | Contenido exigido |
|---|---|
| `rag_tenerife.ipynb` | Completado **y ejecutado en orden**: parámetros, funciones, resultados y **conclusión de 300–500 palabras**. |
| `resultados.json` | Las **12 ejecuciones** (6 preguntas × `k=2` y `k=4`). |
| `revision.csv` | Revisión manual de las 12 (Hit@k, respaldo, citas, abstención, observaciones). |
| `README.md` + `requirements.txt` | Pasos de ejecución, **versión de Python**, dependencias y **nombres** de variables de entorno. |
| `preguntas.csv`, `utilidades.py` | Y cualquier módulo que se añada. |

**Sin** claves, `.env`, entornos virtuales ni cachés. Rúbrica: preparación documental 15 % · recuperación 20 % ·
respuestas respaldadas por evidencia 30 % · evaluación y decisiones 25 % · reproducibilidad 10 %.
No puntúan agentes, memoria multiturno, meteorología, *function calling*, despliegue ni interfaz gráfica.

## 2. Estado actual (marca lo que vayas cerrando)

| ✔ | Paso | Celda del notebook | Test / comando | Doc |
|---|---|---|---|---|
| ✅ | **0 · Entorno** | — | `practica/verificar.sh 0` | [paso-00](./docs/paso-00-entorno.md) |
| ✅ | **1 · Inspección de la carga** | `imports` + markdown | `practica/verificar.sh 1` | [paso-01](./docs/paso-01-inspeccion.md) |
| ✅ | **2 · TODO 4 `hit_pagina`** | `hit_pagina` | `practica/verificar.sh 2` | [paso-02](./docs/paso-02-hit-pagina.md) |
| ✅ | **3 · TODO 1 `fragmentar`** | `fragmentar` + markdown | `practica/verificar.sh 3` | [paso-03](./docs/paso-03-fragmentar.md) |
| ✅ | **4 · TODO 2 `recuperar`** | `recuperar` | `practica/verificar.sh 4` | [paso-04](./docs/paso-04-recuperar.md) |
| ✅ | **5 · TODO 3 `crear_prompt`** | `crear_prompt` + markdown | `practica/verificar.sh 5` | [paso-05](./docs/paso-05-prompt.md) |
| ⬜ | **6 · Modelos `gpt-5-nano`** *(preparado; falta la prueba en vivo)* | `api_setup` + markdown | `practica/verificar.sh 6` | [paso-06](./docs/paso-06-modelos.md) |
| ⬜ | **7 · Índice** *(en vivo)* | `index` | `practica/verificar.sh 7` | [paso-07](./docs/paso-07-indice.md) |
| ⬜ | **8 · Las 12 ejecuciones** *(en vivo)* | `run` | `verificar.sh 8` + validador | [paso-08](./docs/paso-08-ejecuciones.md) |
| ⬜ | **9 · Revisión manual (tú)** | `summary` | `verificar.sh 9` + `--validar` | [paso-09](./docs/paso-09-revision.md) |
| ⬜ | **10 · Conclusión** | celda «### Conclusión» | `verificar.sh 10` + validador | [paso-10](./docs/paso-10-conclusion.md) |
| ⬜ | **11 · Entrega** | todo (kernel limpio) | `verificar.sh` + `empaquetar` | [paso-11](./docs/paso-11-entrega.md) |

Los **pasos 0–5 están implementados y verifican en verde sin red ni coste**. Los pasos 6–11 tienen ya sus herramientas
y tests; lo que queda es ejecutar **en vivo** contra OpenAI (coste bajo) y la parte que es tuya (revisión y aprobar la conclusión).

## 3. Cómo se trabaja

```bash
# desde la raíz del repo
practica/verificar.sh 5       # tests hasta el paso 5 (sin red, sin coste)
practica/verificar.sh         # toda la suite (78 tests)
scripts/practica.sh           # JupyterLab en "practica/Recursos " con la clave de la práctica
```

En VS Code elige el kernel **.venv (Python 3.11)** (o *Python (rag-curso)*) y abre `practica/Recursos /rag_tenerife.ipynb`.

### Antes de las ejecuciones en vivo (pasos 6, 7, 8, 11)

- La clave del sandbox de EBIS está en `practica/Recursos /.env` (**ignorado por git; no se entrega**). Reglas de EBIS:
  **modelo `gpt-5-nano` obligatorio**, presupuesto limitado y **sin bucles**. Total previsto: ~33 embeddings + 12 generaciones.
- **Paso 6 primero**: comprueba con una llamada mínima si la clave permite embeddings (`text-embedding-3-small`).
  Si no, `EMBEDDING_PROVIDER=local` en `Recursos /.env` usa embeddings locales sin coste.
- `gpt-5-nano` no admite `temperature=0`: las respuestas **no son deterministas**. Guarda copia de
  `resultados.json` y `revision.csv` antes de repetir; `revision.csv` **no se sobrescribe**.

## 4. Qué haces tú y qué hace el asistente

| Tarea | Quién |
|---|---|
| Implementar cada paso, sus tests y su doc | Asistente (tú revisas) |
| Ejecutar las celdas en vivo (pasos 6–8, 11) | Tú, o el asistente **cuando lo pidas** |
| **Leer las respuestas y rellenar `revision.csv` (0/1/NA)** | **Tú** (la revisión manual es el corazón de la nota) |
| Redactar la conclusión con las cifras reales | Asistente propone, **tú apruebas/editas** |
| Commits | Solo cuando lo pidas (mensaje sugerido en cada `docs/paso-NN`) |

## 5. Problemas habituales

- `FileNotFoundError: data/TENERIFE.pdf` → abre Jupyter desde `practica/Recursos ` (el nombre **termina en espacio**; usa comillas) y comprueba `data/TENERIFE.pdf`.
- `Configura OPENAI_API_KEY` → arranca con `scripts/practica.sh` (no con `scripts/lab.sh`, que exportaría tu clave personal).
- Una llamada fallida **no** es una abstención correcta: repite (`error_tecnico`).
- El formato de cita que reconoce el código es `[TENERIFE.pdf, p. 15]` **con espacio** (el enunciado lo escribe sin él).
