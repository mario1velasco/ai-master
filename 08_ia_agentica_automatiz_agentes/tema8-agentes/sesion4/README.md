# Sesión 4 · Memoria, contexto y estado

## Demos

| Archivo | Qué muestra |
|---|---|
| `memoria.py` | Memoria a largo plazo por cliente: escribir, recuperar (similitud + recencia) y olvidar |
| `agente_con_memoria.py` | El agente recuerda a cada cliente entre conversaciones distintas |
| `checkpointing.py` | Estado persistente en SQLite: retomar conversaciones, ver el historial y volver atrás |

Memoria entre conversaciones (ejecuta los comandos por separado, como si fueran días distintos):

```bash
python -m sesion4.agente_con_memoria marta.lopez@email.com "Tengo la piel muy sensible y me salen rojeces con algunos productos. ¿Qué tal es el sérum?"
python -m sesion4.agente_con_memoria marta.lopez@email.com "¿Qué me recomendáis para el sol este verano?"
python -m sesion4.agente_con_memoria marta.lopez@email.com --olvidar
```

Checkpointing:

```bash
python -m sesion4.checkpointing --hilo ticket-42 "Soy jorge.ruiz@email.com, ¿cómo va mi pedido?"
python -m sesion4.checkpointing --hilo ticket-42 "¿Y qué producto era?"
python -m sesion4.checkpointing --hilo ticket-42 --historial
python -m sesion4.checkpointing --hilo ticket-42 --volver 2 "Perdona, mi email es marta.lopez@email.com"
```

Los datos se guardan en la carpeta `datos/`. Bórrala para empezar de cero.

## Deberes

**Nivel base · Comprime el historial.** Escribe una función que, cuando la conversación
supere un número de tokens (estímalos como caracteres / 4), sustituya los mensajes
antiguos por un resumen y conserve literales los últimos. Cuidado: no separes nunca
una llamada a herramienta de su resultado.

**Reto · Importancia.** Ahora todas las memorias valen lo mismo. Haz que el modelo
puntúe de 1 a 10 la importancia de cada memoria al guardarla y que la recuperación
la tenga en cuenta junto a la similitud y la recencia.
