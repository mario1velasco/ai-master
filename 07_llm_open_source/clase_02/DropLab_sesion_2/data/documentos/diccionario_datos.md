# DropLab · Diccionario de exportaciones
Documento DAT-2026-04 · Versión 1 · Responsable: equipo de datos
Corte: 26/04/2026. Moneda: EUR. CSV con cabecera, separador coma y punto decimal. Zona horaria: Europe/Madrid.

## Periodos y métricas comerciales
Periodo A: 02/03/2026 a 29/03/2026, ambos incluidos. Periodo B: 30/03/2026 a 26/04/2026, ambos incluidos. Cada periodo tiene 28 días.
Ventas antes de reembolsos = suma de importe_linea por fecha_venta. Los descuentos de caja ya están aplicados en importe_linea.
Reembolsos reconocidos = suma de importe_reembolso por fecha_reconocimiento, asignando tienda y producto mediante la línea original.
Ventas netas = ventas antes de reembolsos menos reembolsos reconocidos en el periodo. Variación = B menos A.
Pedidos = número de pedido_id distintos. Líneas = número de filas de venta. Unidades = suma de cantidad.
Ticket bruto = ventas antes de reembolsos / pedidos. Unidades por pedido = unidades / pedidos. Unidades por línea = unidades / líneas.
Precio realizado por unidad = ventas antes de reembolsos / unidades. El promedio simple de precio_unitario es un promedio de precios de lista por línea.

## locales.csv
Una fila por tienda. Clave: local_id.
| Campo | Definición |
|---|---|
| local_id | Código de tienda. |
| nombre | Nombre comercial del local. |
| ciudad | Ciudad de la tienda. |
| zona_horaria | Zona para interpretar sus horarios. |

## referencias.csv
Una fila por SKU. Un SKU identifica una combinación de modelo, color y talla.
| Campo | Definición |
|---|---|
| sku | Identificador de variante, único en el catálogo. |
| modelo | Familia comercial del producto. |
| color | Color de la variante. |
| categoria | zapatilla, camiseta o sudadera. |
| talla | Talla comercial, tratada como texto. |
| precio_lista | Precio de catálogo por unidad, en EUR. |
| estado_catalogo | Estado del artículo en el catálogo. |
Una unidad de zapatilla es un par. El precio de lista no es el coste de adquisición.

## ventas.csv
Una fila por línea de pedido. linea_id es única; pedido_id puede repetirse. La exportación A/B contiene dos líneas por pedido. Los identificadores no sustituyen al filtro por fecha.
| Campo | Definición |
|---|---|
| linea_id | Clave del renglón de venta. |
| pedido_id | Identificador de la compra completa. |
| fecha_venta | Día en que se registró la venta; sin hora. |
| local_id | Tienda de la venta. |
| sku | Variante vendida; enlaza con referencias.csv. |
| cantidad | Unidades de esa variante. |
| precio_unitario | Precio por unidad antes de descuento. |
| descuento_linea | Descuento monetario total de la línea. |
| importe_linea | cantidad × precio_unitario − descuento_linea. |
| estado_linea | Estado de la línea de venta. |
Un abono posterior se registra aparte, sin eliminar la venta original. La exportación incluye una línea histórica de febrero para enlazar abonos reconocidos en marzo.

## reembolsos.csv
Una fila por evento de abono. Clave: reembolso_id. Una línea de venta puede tener varios abonos.
| Campo | Definición |
|---|---|
| reembolso_id | Identificador único del abono. |
| linea_id | Línea de la compra original. |
| fecha_reconocimiento | Día de reconocimiento del abono. |
| unidades | Artículos devueltos físicamente; puede ser cero. |
| importe_reembolso | Importe positivo abonado, en EUR. |
| motivo | Motivo comercial del abono. |
Para las condiciones de abono, consultar politica_reembolsos.md.

## calendario.csv
Una fila por tienda y día. Clave compuesta: fecha y local_id.
| Campo | Definición |
|---|---|
| fecha | Día de actividad registrado. |
| local_id | Tienda a la que corresponde. |
| abre | Hora de apertura. |
| cierra | Hora de cierre. |
| cobertura_completa | El registro de disponibilidad cubre todo el horario de apertura para los SKU incluidos en esa exportación. |
La cobertura se refiere al alcance exportado: ocho variantes de Street One.

## disponibilidad.csv
Una fila por tienda, SKU e intervalo observado. El inicio está incluido y el fin excluido: inicio ≤ instante < fin.
| Campo | Definición |
|---|---|
| local_id | Tienda observada. |
| sku | Variante observada. |
| inicio | Inicio del intervalo, con offset horario. |
| fin | Fin del intervalo, con offset horario. |
| unidades_disponibles | Disponibilidad registrada durante el intervalo. |
| estado_registro | Estado del registro; observado en esta exportación. |
Se exportan solo los ocho SKU de Street One. Un SKU ausente queda fuera de cobertura. El archivo es una serie de disponibilidad, no un libro de movimientos de almacén. No permite conciliar todas las entradas, reservas y ventas.
Horas-SKU de cero = suma de duraciones por variante. Horas de reloj afectadas = duración de la unión de intervalos por tienda.

## Campos no incluidos
No hay cliente_id, conteos de visitas, hora de venta, costes, margen, campaña aplicada, regalos entregados, reservas perdidas ni demanda no atendida. Los números de pedido no identifican personas.
