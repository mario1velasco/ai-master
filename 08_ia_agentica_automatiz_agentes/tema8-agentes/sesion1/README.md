# Sesión 1 · Del LLM al agente

## Demos

| Archivo | Qué muestra |
|---|---|
| `agente_minimo.py` | Un agente completo sin frameworks: herramientas + bucle + condición de parada |
| `workflow_equivalente.py` | La misma necesidad resuelta como workflow: el código decide los pasos |

Prueba el agente con distintas consultas:

```bash
python -m sesion1.agente_minimo "¿Hay stock de crema hidratante?"
python -m sesion1.agente_minimo "Soy marta.lopez@email.com, ¿qué pedidos tengo?"
python -m sesion1.agente_minimo "Quiero 10 sérums de vitamina C y 10 protectores solares, ¿hay suficientes?"
python -m sesion1.agente_minimo --max-iter 20 "¿Dónde está mi envío TRK-58873? Insiste hasta que funcione."
```

Y compáralo con el workflow:

```bash
python -m sesion1.workflow_equivalente "Hola, soy marta.lopez@email.com, ¿cómo van mis pedidos?"
```

## Deberes

No son evaluables. Los comentaremos al inicio de la sesión 2.

**Nivel base · Añade una herramienta.** El agente no puede consultar un pedido
por su número. Añade la herramienta `consultar_pedido`, que use la función
`tienda.obtener_pedido` ya existente. Pista: necesitas añadir una entrada en
`HERRAMIENTAS` y otra en `FUNCIONES`; el bucle no cambia. Comprueba que funciona
con: «¿En qué estado está el pedido ORD-10544?».

**Reto · Detecta bucles.** Cuando el transportista no responde, el agente puede
repetir la misma llamada hasta agotar el límite de pasos. Haz que, si una
herramienta se llama más de dos veces con los mismos argumentos, el agente deje
de intentarlo y explique al cliente qué ocurre. Pista: no hace falta tocar el
bucle.

**Pregunta para pensar:** ¿cuál de las dos versiones (agente o workflow) pondrías
en producción para responder a «¿cómo van mis pedidos?», y por qué?
