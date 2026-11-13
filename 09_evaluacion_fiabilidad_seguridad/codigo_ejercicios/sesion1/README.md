# Sesión 1 · Medir al agente: métricas, pruebas y benchmarks

## Demos

| Archivo | Qué muestra |
|---|---|
| `casos.json` | El conjunto de pruebas: 12 casos normales, de borde y adversarios, con lo que se espera de cada uno |
| `medir.py` | Calidad, fiabilidad (pass^k), latencia, disponibilidad y coste del agente |
| `evaluar.py` | Tres formas de evaluar un caso: resultado, trayectoria y juez LLM con rúbrica |
| `etiquetas_humanas.json` | 10 respuestas etiquetadas por una persona (para el reto) |

```bash
python -m sesion1.medir
python -m sesion1.medir --repeticiones 3
python -m sesion1.medir --categoria adversario
python -m sesion1.evaluar
python -m sesion1.evaluar N3 B2 A1
```

## Deberes

No son evaluables. Los comentaremos al inicio de la sesión 2.

**Nivel base · Amplía el conjunto de pruebas.** Añade cuatro casos nuevos, al
menos uno de cada categoría (normal, borde y adversario), y una métrica nueva:
**coste por caso resuelto** (los tokens de todos los intentos entre los casos
que se han resuelto bien). En la demo de MLflow del Tema 8 calculasteis el coste
total de un run; aquí la pregunta es otra: cuánto cuesta cada acierto. Ejecuta la medición y compárala con el coste por caso.

**Reto · Calibra el juez.** Un juez LLM también se equivoca. Pásale las diez
respuestas de `etiquetas_humanas.json` y calcula el acuerdo con la persona y
cuántas respuestas malas aprueba (falsos positivos). Cambia la rúbrica o el
prompt del juez y comprueba si mejora.
