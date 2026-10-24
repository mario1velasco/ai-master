# Paso 10 · Conclusión (300–500 palabras)

> Redacta la conclusión con las cifras reales de la revisión.

## Qué hemos hecho

Una celda markdown que empieza por **`### Conclusión`**, con: decisiones de fragmentación y recuperación; **tabla de las 4 métricas por k** (Hit@k, respaldo, citas, abstención); un caso concreto (Q1–Q6); configuración recomendada; **una limitación y una mejora** ligadas a un fallo observado. **Solo se puede escribir con las cifras reales de `resumen_revision()`**. No hace falta que `k=4` supere a `k=2`.

## Cómo ejecutarlo

```bash
practica/verificar.sh 10
cd practica && ../.venv/bin/python -m herramientas.validar_conclusion "Recursos /rag_tenerife.ipynb"
```

## En qué clase nos fijamos

- [Sesión 6 · §14–15 (qué se puede y no se puede concluir; límites del experimento)](../../clases/06-Const-evaluacion/EXPLICACION_sesion_06.md)
- [Sesión 3 · §6 Reciprocal Rank Fusion (mejora posible: búsqueda híbrida)](../../clases/03-recuper-info-2/EXPLICACION_sesion_03.md)
- [Sesión 7 · §16 ¿Qué sigue después? (reranking, más preguntas de evaluación)](../../clases/07-RAG/EXPLICACION_sesion_07.md)

## Celda(s) del notebook rellenadas

Celda markdown final `8694e9f2` («7 Análisis y recomendación») + **nueva celda** «### Conclusión».
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

`validar_conclusion` sin problemas.

## Commit sugerido

- **Mensaje:** `Redacta la conclusión con las cifras reales`
- **Ficheros:** `practica/herramientas/validar_conclusion.py`, `practica/tests/test_paso_10_conclusion.py`, `Recursos /rag_tenerife.ipynb`
