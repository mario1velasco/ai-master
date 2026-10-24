# Sesión 2 · Razonar y actuar: ReAct y patrones de planificación

## Demos

| Archivo | Qué muestra |
|---|---|
| `react_prompting.py` | ReAct implementado a mano: el modelo escribe Pensamiento / Acción / Entrada y nuestro código interpreta el texto |
| `plan_and_execute.py` | Un planificador descompone la tarea, un ejecutor resuelve cada paso y un sintetizador responde |
| `reflexion.py` | Un crítico revisa la respuesta con criterios explícitos y el agente la rehace si no la aprueba |
| `comparar_estrategias.py` | La misma tarea con las cuatro estrategias: llamadas, tokens y tiempo |

```bash
python -m sesion2.react_prompting "Soy marta.lopez@email.com, ¿puedo repetir mi último pedido?"
python -m sesion2.plan_and_execute "Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?"
python -m sesion2.reflexion "Quiero comprar 10 protectores solares, ¿me los enviáis?"
python -m sesion2.comparar_estrategias
```

## Deberes

**Nivel base · Reflexión en el plan-and-execute.** Antes de devolver la síntesis
final del plan-and-execute, haz que el crítico de `reflexion.py` la revise y, si no
la aprueba, vuelve a sintetizar con sus comentarios. Pista: puedes reutilizar
`planificar`, `ejecutar_paso`, `sintetizar` y `criticar` sin modificarlas.

**Reto · Replanificación.** Si un paso falla (por ejemplo, el transportista no
responde), el plan sigue adelante como si nada. Añade un verificador que decida
si cada paso se ha completado y, si no, pide al planificador un plan nuevo para lo
que queda. Limita el número de replanificaciones.
Prueba: «¿Dónde está el último pedido de marta.lopez@email.com?».
