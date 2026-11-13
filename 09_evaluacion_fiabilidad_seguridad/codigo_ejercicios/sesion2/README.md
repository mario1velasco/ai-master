# Sesión 2 · Fallos, guardarraíles y seguridad

## Demos

| Archivo | Qué muestra |
|---|---|
| `alucinaciones.py` | Detectar datos inventados comprobando la respuesta contra lo que devolvieron las herramientas |
| `guardarrailes.py` | Los cuatro puntos de control: entrada, herramientas, resultados y salida |
| `permisos.py` | Mínimo privilegio: perfiles de herramientas y alcance limitado al cliente autenticado |
| `inyeccion.py` | Una inyección de prompt indirecta escondida en una reseña, sin y con defensas |

```bash
python -m sesion2.alucinaciones
python -m sesion2.alucinaciones "¿Cuánto cuesta el champú?"
python -m sesion2.permisos
python -m sesion2.inyeccion
python -m sesion2.inyeccion --defensas
```

Todo es simulado: los emails solo se guardan en una lista y los reembolsos no son reales.

## Deberes

**Nivel base · Un guardarraíl contra datos inventados.** Usa el detector de
`alucinaciones.py` para crear un guardarraíl de salida: si la respuesta contiene
un precio, una cantidad, un pedido o un plazo que no aparece en los resultados de
las herramientas, no se envía y sale una respuesta segura. Pruébalo con
«¿Tenéis champú? ¿A qué precio?».

**Reto · Sigue la procedencia del contenido.** Marcar las reseñas como no
fiables ayuda, pero el modelo puede seguir obedeciéndolas. Haz que, en cuanto el
agente haya leído contenido escrito por terceros en una conversación, las
herramientas irreversibles queden bloqueadas en esa conversación. Compruébalo
con `inyeccion.py` dando al agente todas las herramientas.
