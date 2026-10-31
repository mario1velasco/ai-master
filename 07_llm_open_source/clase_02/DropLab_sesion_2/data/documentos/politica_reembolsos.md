# DropLab · Política comercial de reembolsos
Documento COM-REF-2026-01 · Versión 1 · Vigente desde 01/02/2026
Responsable: atención al cliente y administración.

## Devolución física
Se admiten solicitudes dentro de los 30 días siguientes a la compra. El registro indica las unidades devueltas y el importe abonado. La operación original permanece en caja.

## Ajustes comerciales
Un ajuste puede devolver parte del importe sin devolución física. En esos casos se registra unidades=0 y motivo=ajuste_comercial. Pueden existir varios ajustes sobre la misma línea; cada uno tiene su propio reembolso_id.

## Reconocimiento
Administración registra cada abono en fecha_reconocimiento. El informe de ventas netas descuenta los abonos reconocidos durante el periodo, incluso cuando la compra corresponde a una fecha anterior. Para localizar tienda y artículo se consulta linea_id en la exportación de ventas.
El análisis de devoluciones de un grupo de compras se solicita por separado, siguiendo las compras originales y sus abonos posteriores.
