# Ejercicio 3 · Ejecuciones reales en el Jetson del aula

Para quien no pueda ejecutar el modelo en su equipo. Se generaron el 03/10/2026 con `herramientas.py`
(con `cesta()` ya completada) y el modelo `qwen3:4b-instruct`, salvo el experimento 3.
Es exactamente lo que verías en tu terminal: qué pide el modelo, qué devuelve el código y qué responde.
Revísalas con las tres comprobaciones del paso 3: herramienta, argumentos y respuesta.

## Base (paso 3)

Orden: `python herramientas.py bateria` · modelo `qwen3:4b-instruct`

### Pregunta 1 · ¿Cuáles fueron las ventas netas de Eixample en el periodo A y en el periodo B?

- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2026-03-02", "hasta": "2026-03-29", "ventas_antes_reembolsos_eur": 25000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 24000.0}`
- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2026-03-30", "hasta": "2026-04-26", "ventas_antes_reembolsos_eur": 26000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 25000.0}`

**Respuesta del modelo** (35.5 s):

> En el periodo A (2026-03-02 al 2026-03-29), las ventas netas de Eixample fueron de 24.000 euros. En el periodo B (2026-03-30 al 2026-04-26), las ventas netas de Eixample fueron de 25.000 euros.

### Pregunta 2 · ¿Cuántos pedidos hizo Goya en el periodo B y cuántas unidades llevaba de media cada pedido?

- El modelo pide `cesta({"local_id": "MAD-GOY", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-GOY", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 307, "unidades_por_pedido": 2.56, "ticket_medio_eur": 258.33, "pedidos_4_o_mas_unidades": 10}`

**Respuesta del modelo** (11.4 s):

> En el periodo B, Goya realizó 120 pedidos, con un promedio de 2.56 unidades por pedido.

### Pregunta 3 · ¿Qué ha cambiado en las compras de Malasaña entre el periodo A y el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29", "pedidos": 120, "lineas": 240, "unidades": 467, "unidades_por_pedido": 3.89, "ticket_medio_eur": 350.0, "pedidos_4_o_mas_unidades": 108}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 304, "unidades_por_pedido": 2.53, "ticket_medio_eur": 233.33, "pedidos_4_o_mas_unidades": 7}`

**Respuesta del modelo** (29.5 s):

> En Malasaña, entre el periodo A y el periodo B, el número de pedidos se mantuvo igual (120), pero el número total de unidades disminuyó de 467 a 304. El ticket medio bajó de 350,00 euros a 233,33 euros. Además, los pedidos con 4 o más unidades pasaron de 108 a solo 7. La media de unidades por pedido disminuyó de 3,89 a 2,53.

### Pregunta 4 · ¿Cuántos pedidos de 4 o más unidades hubo en Malasaña en el periodo A y en el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29", "pedidos": 120, "lineas": 240, "unidades": 467, "unidades_por_pedido": 3.89, "ticket_medio_eur": 350.0, "pedidos_4_o_mas_unidades": 108}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 304, "unidades_por_pedido": 2.53, "ticket_medio_eur": 233.33, "pedidos_4_o_mas_unidades": 7}`

**Respuesta del modelo** (25.9 s):

> En el periodo A (2026-03-02 al 2026-03-29), hubo 108 pedidos de 4 o más unidades en Malasaña. En el periodo B (2026-03-30 al 2026-04-26), hubo 7 pedidos de 4 o más unidades en Malasaña.

### Pregunta 5 · ¿Cuánto vendió Malasaña, en ventas netas, entre el 6 y el 12 de abril de 2026?

- El modelo pide `ventas_netas({"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12", "ventas_antes_reembolsos_eur": 6213.48, "reembolsos_reconocidos_eur": 911.11, "ventas_netas_eur": 5302.37}`

**Respuesta del modelo** (12.9 s):

> Malasaña vendió 5.302,37 euros en ventas netas entre el 6 y el 12 de abril de 2026.

### Pregunta 6 · ¿Cuántas personas visitaron la tienda de Malasaña en abril?

- El modelo **no ha pedido ninguna herramienta**.

**Respuesta del modelo** (5.4 s):

> No puedo determinar el número de personas que visitaron la tienda de Malasaña en abril, ya que no hay herramientas disponibles para obtener datos sobre el número de visitantes o personas.

## Experimento 1 · Descripciones pobres

Orden: `python herramientas.py bateria --descripciones-pobres` · modelo `qwen3:4b-instruct`

### Pregunta 1 · ¿Cuáles fueron las ventas netas de Eixample en el periodo A y en el periodo B?

- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2026-03-02", "hasta": "2026-03-29", "ventas_antes_reembolsos_eur": 25000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 24000.0}`
- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2026-03-30", "hasta": "2026-04-26", "ventas_antes_reembolsos_eur": 26000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 25000.0}`

**Respuesta del modelo** (27.3 s):

> En el periodo A (2026-03-02 al 2026-03-29), las ventas netas de Eixample fueron de 24.000 €. En el periodo B (2026-03-30 al 2026-04-26), las ventas netas de Eixample fueron de 25.000 €.

### Pregunta 2 · ¿Cuántos pedidos hizo Goya en el periodo B y cuántas unidades llevaba de media cada pedido?

- El modelo pide `cesta({"local_id": "MAD-GOY", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-GOY", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 307, "unidades_por_pedido": 2.56, "ticket_medio_eur": 258.33, "pedidos_4_o_mas_unidades": 10}`

**Respuesta del modelo** (11.4 s):

> En el periodo B, Goya realizó 120 pedidos, con un promedio de 2.56 unidades por pedido.

### Pregunta 3 · ¿Qué ha cambiado en las compras de Malasaña entre el periodo A y el periodo B?

- El modelo pide `ventas_netas({"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29", "ventas_antes_reembolsos_eur": 42000.0, "reembolsos_reconocidos_eur": 2000.0, "ventas_netas_eur": 40000.0}`
- El modelo pide `ventas_netas({"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26", "ventas_antes_reembolsos_eur": 28000.0, "reembolsos_reconocidos_eur": 2000.0, "ventas_netas_eur": 26000.0}`

**Respuesta del modelo** (35.3 s):

> En el periodo A (2026-03-02 al 2026-03-29), las ventas netas en Malasaña fueron de 40.000 €. En el periodo B (2026-03-30 al 2026-04-26), las ventas netas descendieron a 26.000 €. Esto representa una reducción de 14.000 € en las ventas netas. No se proporciona información sobre cambios en el número de compras o el comportamiento del cliente. El cambio indica una disminución significativa en las compras en Malasaña entre ambos periodos.

### Pregunta 4 · ¿Cuántos pedidos de 4 o más unidades hubo en Malasaña en el periodo A y en el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29", "pedidos": 120, "lineas": 240, "unidades": 467, "unidades_por_pedido": 3.89, "ticket_medio_eur": 350.0, "pedidos_4_o_mas_unidades": 108}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 304, "unidades_por_pedido": 2.53, "ticket_medio_eur": 233.33, "pedidos_4_o_mas_unidades": 7}`

**Respuesta del modelo** (26.8 s):

> En el periodo A (2026-03-02 al 2026-03-29), hubo 108 pedidos de 4 o más unidades en Malasaña. En el periodo B (2026-03-30 al 2026-04-26), hubo 7 pedidos de 4 o más unidades en Malasaña.

### Pregunta 5 · ¿Cuánto vendió Malasaña, en ventas netas, entre el 6 y el 12 de abril de 2026?

- El modelo pide `ventas_netas({"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12", "ventas_antes_reembolsos_eur": 6213.48, "reembolsos_reconocidos_eur": 911.11, "ventas_netas_eur": 5302.37}`

**Respuesta del modelo** (12.4 s):

> Malasaña vendió 5.302,37 euros en ventas netas entre el 6 y el 12 de abril de 2026.

### Pregunta 6 · ¿Cuántas personas visitaron la tienda de Malasaña en abril?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-04-01", "hasta": "2026-04-30"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-04-01", "hasta": "2026-04-30", "pedidos": 110, "lineas": 220, "unidades": 279, "unidades_por_pedido": 2.54, "ticket_medio_eur": 233.34, "pedidos_4_o_mas_unidades": 6}`

**Respuesta del modelo** (17.7 s):

> En abril, 110 personas realizaron pedidos en la tienda de Malasaña. El total de unidades vendidas fue de 279, con un ticket medio de 233,34 euros. Se registraron 6 pedidos con 4 o más unidades. No se proporciona el número exacto de visitantes únicos, solo el número de pedidos.

## Experimento 2 · Sin contexto

Orden: `python herramientas.py bateria --sin-contexto` · modelo `qwen3:4b-instruct`

### Pregunta 1 · ¿Cuáles fueron las ventas netas de Eixample en el periodo A y en el periodo B?

- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2023-01-01", "hasta": "2023-03-31"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2023-01-01", "hasta": "2023-03-31", "ventas_antes_reembolsos_eur": 0.0, "reembolsos_reconocidos_eur": 0.0, "ventas_netas_eur": 0.0}`
- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2023-04-01", "hasta": "2023-06-30"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2023-04-01", "hasta": "2023-06-30", "ventas_antes_reembolsos_eur": 0.0, "reembolsos_reconocidos_eur": 0.0, "ventas_netas_eur": 0.0}`

**Respuesta del modelo** (25.4 s):

> Las ventas netas de Eixample en el periodo A (enero-marzo de 2023) fueron de 0,0 euros. Las ventas netas de Eixample en el periodo B (abril-junio de 2023) también fueron de 0,0 euros.

### Pregunta 2 · ¿Cuántos pedidos hizo Goya en el periodo B y cuántas unidades llevaba de media cada pedido?

- El modelo pide `cesta({"local_id": "MAD-GOY", "desde": "2023-04-01", "hasta": "2023-04-30"})`
  - El código devuelve `{"local_id": "MAD-GOY", "desde": "2023-04-01", "hasta": "2023-04-30", "pedidos": 0, "lineas": 0, "unidades": 0, "unidades_por_pedido": null, "ticket_medio_eur": null, "pedidos_4_o_mas_unidades": 0}`

**Respuesta del modelo** (12.9 s):

> En el periodo de abril de 2023, Goya no tuvo pedidos (0 pedidos) y no se puede determinar el número de unidades por pedido porque el dato está nulo.

### Pregunta 3 · ¿Qué ha cambiado en las compras de Malasaña entre el periodo A y el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2023-01-01", "hasta": "2023-12-31"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2023-01-01", "hasta": "2023-12-31", "pedidos": 0, "lineas": 0, "unidades": 0, "unidades_por_pedido": null, "ticket_medio_eur": null, "pedidos_4_o_mas_unidades": 0}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2024-01-01", "hasta": "2024-12-31"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2024-01-01", "hasta": "2024-12-31", "pedidos": 0, "lineas": 0, "unidades": 0, "unidades_por_pedido": null, "ticket_medio_eur": null, "pedidos_4_o_mas_unidades": 0}`

**Respuesta del modelo** (23.1 s):

> No hay datos de compras en Malasaña para los periodos 2023 y 2024, ya que el número de pedidos, líneas, unidades y ticket medio son todos cero. No se puede determinar un cambio porque no hay información disponible para ninguno de los periodos.

### Pregunta 4 · ¿Cuántos pedidos de 4 o más unidades hubo en Malasaña en el periodo A y en el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2023-01-01", "hasta": "2023-12-31"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2023-01-01", "hasta": "2023-12-31", "pedidos": 0, "lineas": 0, "unidades": 0, "unidades_por_pedido": null, "ticket_medio_eur": null, "pedidos_4_o_mas_unidades": 0}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2024-01-01", "hasta": "2024-12-31"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2024-01-01", "hasta": "2024-12-31", "pedidos": 0, "lineas": 0, "unidades": 0, "unidades_por_pedido": null, "ticket_medio_eur": null, "pedidos_4_o_mas_unidades": 0}`

**Respuesta del modelo** (22.7 s):

> En el periodo 2023, en Malasaña, hubo 0 pedidos con 4 o más unidades. En el periodo 2024, en Malasaña, también hubo 0 pedidos con 4 o más unidades.

### Pregunta 5 · ¿Cuánto vendió Malasaña, en ventas netas, entre el 6 y el 12 de abril de 2026?

- El modelo pide `ventas_netas({"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12", "ventas_antes_reembolsos_eur": 6213.48, "reembolsos_reconocidos_eur": 911.11, "ventas_netas_eur": 5302.37}`

**Respuesta del modelo** (12.5 s):

> Malasaña vendió 5.302,37 euros en ventas netas entre el 6 y el 12 de abril de 2026.

### Pregunta 6 · ¿Cuántas personas visitaron la tienda de Malasaña en abril?

- El modelo **no ha pedido ninguna herramienta**.

**Respuesta del modelo** (5.2 s):

> No puedo determinar el número de personas que visitaron la tienda de Malasaña en abril, ya que no hay herramientas disponibles para obtener datos sobre el número de visitantes o personas.

## Experimento 3 · Otro modelo

Orden: `python herramientas.py bateria --modelo llama3.2:3b` · modelo `llama3.2:3b`

### Pregunta 1 · ¿Cuáles fueron las ventas netas de Eixample en el periodo A y en el periodo B?

- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2026-03-02", "hasta": "2026-03-29", "ventas_antes_reembolsos_eur": 25000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 24000.0}`
- El modelo pide `ventas_netas({"local_id": "BCN-EIX", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "BCN-EIX", "desde": "2026-03-30", "hasta": "2026-04-26", "ventas_antes_reembolsos_eur": 26000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 25000.0}`

**Respuesta del modelo** (19.0 s):

> Las ventas netas de Eixample en el periodo A fueron de 24.000 euros y en el periodo B fueron de 25.000 euros.

### Pregunta 2 · ¿Cuántos pedidos hizo Goya en el periodo B y cuántas unidades llevaba de media cada pedido?

- El modelo pide `cesta({"hasta": "2026-04-26", "local_id": "MAD-GOY", "desde": "2026-03-30"})`
  - El código devuelve `{"local_id": "MAD-GOY", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 307, "unidades_por_pedido": 2.56, "ticket_medio_eur": 258.33, "pedidos_4_o_mas_unidades": 10}`

**Respuesta del modelo** (7.0 s):

> En el periodo B, Goya hizo 120 pedidos y la media de unidades por pedido fue de 2.56 unidades.

### Pregunta 3 · ¿Qué ha cambiado en las compras de Malasaña entre el periodo A y el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29", "pedidos": 120, "lineas": 240, "unidades": 467, "unidades_por_pedido": 3.89, "ticket_medio_eur": 350.0, "pedidos_4_o_mas_unidades": 108}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 304, "unidades_por_pedido": 2.53, "ticket_medio_eur": 233.33, "pedidos_4_o_mas_unidades": 7}`

**Respuesta del modelo** (19.7 s):

> Entre el periodo A y el periodo B, se ha observado una disminución en la cantidad de pedidos en Malasaña, pasando de 120 pedidos en el periodo A a 120 pedidos en el periodo B. Sin embargo, la cantidad de unidades vendidas ha disminuido más, pasando de 467 unidades en el periodo A a 304 unidades en el periodo B. Además, el ticket medio ha disminuido, pasando de 350 euros en el periodo A a 233,33 euros en el periodo B.

### Pregunta 4 · ¿Cuántos pedidos de 4 o más unidades hubo en Malasaña en el periodo A y en el periodo B?

- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-02", "hasta": "2026-03-29", "pedidos": 120, "lineas": 240, "unidades": 467, "unidades_por_pedido": 3.89, "ticket_medio_eur": 350.0, "pedidos_4_o_mas_unidades": 108}`
- El modelo pide `cesta({"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-03-30", "hasta": "2026-04-26", "pedidos": 120, "lineas": 240, "unidades": 304, "unidades_por_pedido": 2.53, "ticket_medio_eur": 233.33, "pedidos_4_o_mas_unidades": 7}`

**Respuesta del modelo** (12.1 s):

> En el periodo A, en Malasaña hubo 108 pedidos de 4 o más unidades. 
> 
> En el periodo B, en Malasaña hubo 7 pedidos de 4 o más unidades.

### Pregunta 5 · ¿Cuánto vendió Malasaña, en ventas netas, entre el 6 y el 12 de abril de 2026?

- El modelo pide `ventas_netas({"desde": "2026-04-06", "hasta": "2026-04-12", "local_id": "MAD-MAL"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-04-06", "hasta": "2026-04-12", "ventas_antes_reembolsos_eur": 6213.48, "reembolsos_reconocidos_eur": 911.11, "ventas_netas_eur": 5302.37}`

**Respuesta del modelo** (7.7 s):

> En el período del 6 al 12 de abril de 2026, Malasaña (MAD-MAL) registró ventas netas de 5302.37 euros.

### Pregunta 6 · ¿Cuántas personas visitaron la tienda de Malasaña en abril?

- El modelo pide `ventas_netas({"desde": "2026-04-01", "hasta": "2026-04-30", "local_id": "MAD-MAL"})`
  - El código devuelve `{"local_id": "MAD-MAL", "desde": "2026-04-01", "hasta": "2026-04-30", "ventas_antes_reembolsos_eur": 25667.27, "reembolsos_reconocidos_eur": 2000.0, "ventas_netas_eur": 23667.27}`

**Respuesta del modelo** (7.4 s):

> En abril, la tienda MAD-MAL de Malasaña recibió un total de 23.667 visitantes.
