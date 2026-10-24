# Paso 1 · Inspección de la carga

> Ejecutar la carga del PDF y documentar las limitaciones de extracción (25 páginas, 24 con texto, página 7 sin texto, texto plano).

## Qué hemos hecho

Se ejecuta `cargar_paginas` (ya suministrada) y se **añade una celda markdown** con lo observado: 25 páginas, 24 con texto, **página 7 sin texto extraíble**, páginas casi vacías (2, 6, 13, 19, 20), sin imágenes ni enlaces y tono coloquial con datos sin fecha. Se conserva la numeración física original.

## Cómo ejecutarlo

```bash
practica/verificar.sh 1
```
O en el notebook, ejecutar la celda `imports` y leer `{'paginas_pdf': 25, 'paginas_con_texto': 24, 'paginas_sin_texto': [7]}`.

## En qué clase nos fijamos

- [Sesión 5 · §2 Un vector rara vez viaja solo: el registro (id, contenido, metadatos)](../../clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md)
- [Sesión 6 · §8 Preparación: el texto común y los límites del recorte](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)

## Celda(s) del notebook rellenadas

Celda `imports` (`f1053357`) ejecutada; **nueva celda markdown** justo debajo con la inspección.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

10 tests OK (pasos 0–1). `page` va de 1 a 25 sin la 7 y `source == 'TENERIFE.pdf'`.

## Commit sugerido

- **Mensaje:** `Documenta la inspección de la carga y sus limitaciones de extracción`
- **Ficheros:** `practica/tests/test_paso_01_inspeccion.py`, `practica/Recursos /rag_tenerife.ipynb`
