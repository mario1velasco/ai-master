# Paso 9 · Revisión manual (la haces tú)

> Lee cada respuesta, compárala con lo que dice la guía y rellena `revision.csv`.

## Qué hemos hecho

`herramientas/preparar_revision.py` imprime por caso: pregunta, **respuesta esperada según la guía**, páginas y texto de los fragmentos recuperados y la respuesta del modelo. Tú rellenas `revision.csv` con **0/1/NA**: `respaldo` y `citas` (Q1–Q4), `abstencion` (Q5–Q6); las celdas vacías son pendientes, no ceros. Después, `resumen_revision()`.

## Cómo ejecutarlo

```bash
practica/verificar.sh 9
cd practica && ../.venv/bin/python -m herramientas.preparar_revision "Recursos /resultados.json" | less
cd practica && ../.venv/bin/python -m herramientas.preparar_revision --validar "Recursos /revision.csv"
```

## En qué clase nos fijamos

- [Sesión 7 · §8 Evaluar un RAG: por etapas y sin trampas (revisión humana, «cita válida ≠ fidelidad»)](../../clases/07-RAG/EXPLICACION_sesion_07.md)
- [Sesión 6 · §4 «Sin juicio» no es lo mismo que «irrelevante»](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)

## Celda(s) del notebook rellenadas

Celda `summary` (`ba0cd50f`, `resumen_revision()`): se ejecuta tras completar `revision.csv`.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

Sin problemas en `--validar` y `resumen_revision()` sin «pendiente de revisar».

## Commit sugerido

- **Mensaje:** `Añade la ayuda de revisión manual y el validador de revision.csv`
- **Ficheros:** `practica/herramientas/preparar_revision.py`, `practica/tests/test_paso_09_revision.py`, `Recursos /revision.csv`
