# Paso 11 · Reproducibilidad y entrega

> Ejecuta desde un kernel limpio, actualiza README/requirements y empaqueta el ZIP.

## Qué hemos hecho

1. En el notebook: **Restart & Run All** (kernel limpio) con la clave de la práctica; guardar las salidas.
2. Actualizar `Recursos /README.md` y `requirements.txt` con pasos de ejecución, **Python 3.11**, dependencias y **nombres** de variables (`OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `EMBEDDING_PROVIDER`), **sin claves**.
3. `herramientas/empaquetar.py` crea `Apellidos_Nombre_RAG_Tenerife.zip` con **solo** los 7 archivos exigidos y se niega si falta alguno o si detecta una clave `sk-…`.

## Cómo ejecutarlo

```bash
practica/verificar.sh            # toda la suite
cd practica && ../.venv/bin/python -m herramientas.empaquetar Velasco_Alonso_Mario
```
(El orden de apellidos y nombre hay que confirmarlo.)

## En qué clase nos fijamos

- [Raíz `CLAUDE.md` §6.6 (entregable y rúbrica de la práctica)](../../CLAUDE.md)
- [Sesión 6 · §16 Arquitectura del laboratorio (huellas y reproducibilidad)](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)

## Celda(s) del notebook rellenadas

Todo el notebook (Restart & Run All).
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

El ZIP contiene exactamente `rag_tenerife.ipynb`, `resultados.json`, `revision.csv`, `README.md`, `requirements.txt`, `preguntas.csv` y `utilidades.py`.

## Commit sugerido

- **Mensaje:** `Prepara la entrega: README, requirements y empaquetado`
- **Ficheros:** `practica/herramientas/empaquetar.py`, `practica/tests/test_paso_11_entrega.py`, `Recursos /README.md`, `Recursos /requirements.txt`
