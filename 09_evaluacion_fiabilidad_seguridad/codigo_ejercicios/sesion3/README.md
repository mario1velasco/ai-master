# Sesión 3 · Observabilidad, supervisión y mejora continua

## Demos

| Archivo | Qué muestra |
|---|---|
| `observabilidad.py` | Logs estructurados, métricas, trazas (también en MLflow) y un registro de auditoría a prueba de manipulaciones |
| `supervision.py` | Una política de aprobación por riesgo, la cola de aprobaciones y la revisión por muestreo |
| `ataques.json` + `red_teaming.py` | Ocho ataques (uno por riesgo del OWASP Top 10 para LLM) contra el agente sin y con defensas |
| `incidente.py` | La cronología del incidente T-77 para hacer un postmortem en clase |

```bash
python -m sesion3.observabilidad
python -m sesion3.observabilidad --informe
python -m sesion3.observabilidad --verificar
python -m sesion3.observabilidad --manipular
python -m sesion3.observabilidad --verificar
python -m sesion3.supervision
python -m sesion3.supervision --pendientes
python -m sesion3.supervision --aprobar A-1
python -m sesion3.red_teaming
python -m sesion3.incidente
```

Las trazas en MLflow ya las trabajasteis en la demo `tema8-mlflow` del Tema 8. Si la
tienes montada y quieres ver estos tickets también allí: `pip install mlflow`,
`python -m sesion3.observabilidad --mlflow` y
`mlflow ui --backend-store-uri sqlite:///datos/mlflow.db --port 5001`. Es opcional:
lo nuevo de esta sesión son la auditoría, las alertas y qué no registrar.

## Deberes finales del tema

**Nivel base · Alertas.** Escribe reglas que, a partir de las métricas de los
logs, avisen cuando la latencia p95 supera un umbral, hay muchos errores
técnicos, se dispara el número de bloqueos de guardarraíles o hay más acciones
irreversibles de lo habitual.

**Reto · Cierra el ciclo de mejora continua.** Convierte cada ataque con éxito de
`datos/regresion.json` en un caso de prueba del conjunto de la sesión 1 y mide el
agente con y sin defensas sobre esos casos y sobre los casos normales. Las
defensas tienen que resolver los ataques **sin empeorar** los casos normales.

**Proyecto (opcional) · Informe de fiabilidad de tu agente.** Aplica lo del
tema a un agente propio o al del Tema 8: conjunto de pruebas, métricas, tres
guardarraíles, una política de supervisión y una batería de cinco ataques.
Resúmelo en una página.
