# Paso 8 · Las 12 ejecuciones

> Ejecuta las 6 preguntas con `k=2` y `k=4` y valida `resultados.json`.

## Qué hemos hecho

La celda `run` llama a `ejecutar_pruebas`: **12 recuperaciones + 12 generaciones** con `gpt-5-nano`. `herramientas/validar_resultados.py` comprueba estructura (12 entradas únicas, sin `error_tecnico`, `k` fragmentos, `hit_pagina` solo en Q1–Q4) y da **avisos** (formato de cita, abstención probable). Un fallo técnico **no** es una abstención: hay que repetir.

## Cómo ejecutarlo

```bash
practica/verificar.sh 8     # valida el validador con una ejecución simulada
# EN VIVO (coste bajo, 12 generaciones): ejecutar la celda `run` del notebook y después
cd practica && ../.venv/bin/python -m herramientas.validar_resultados "Recursos /resultados.json"
```
⚠️ Antes de repetir, guarda copia de `resultados.json` y `revision.csv` (el segundo **no se sobrescribe**).

## En qué clase nos fijamos

- [Sesión 7 · §9 Resultados reales de la comparación (leer costes y latencias con cautela)](../../clases/07-RAG/EXPLICACION_sesion_07.md)
- [Sesión 6 · §14 La reserva final: no usar una sola prueba](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)

## Celda(s) del notebook rellenadas

Celda `run` (`7f09667d`): sin cambios de código; se ejecuta en vivo y **guarda sus salidas**.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

`validar_resultados` sin errores; los avisos son indicios para la revisión.

## Commit sugerido

- **Mensaje:** `Añade el validador de resultados.json y ejecuta las 12 pruebas`
- **Ficheros:** `practica/herramientas/validar_resultados.py`, `practica/tests/simulacion.py`, `practica/tests/test_paso_08_resultados.py`, (`Recursos /resultados.json` y `revision.csv` tras la ejecución en vivo)
