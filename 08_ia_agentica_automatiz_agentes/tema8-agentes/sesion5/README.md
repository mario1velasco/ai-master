# Sesión 5 · Sistemas multiagente

## Demo

`equipo_supervisor.py`: un supervisor coordina a tres agentes especializados
(clasificador, logística y redactor). Al final muestra cuántos tokens ha gastado cada uno.

```bash
python -m sesion5.equipo_supervisor "Soy marta.lopez@email.com. Mi pedido ORD-10544 no llega y lo necesito para un regalo el viernes."
python -m sesion5.equipo_supervisor "¿Os queda crema hidratante?"
```

Fíjate en la segunda: ¿necesitaba un equipo de cuatro agentes?

## Deberes

**Nivel base · Un cuarto agente.** Añade un agente de devoluciones que aplique la
política de la tienda y proponga, sin emitirlo, un reembolso. Pista: solo hay que
crear su función y añadirlo al diccionario `AGENTES`; el supervisor lo descubre por
su descripción.

**Reto · ¿Compensa?** Ejecuta el mismo ticket con un agente único (todas las
herramientas, un solo prompt) y con el equipo. Compara tokens y calidad de la
respuesta. ¿En qué tickets merece la pena el equipo?
