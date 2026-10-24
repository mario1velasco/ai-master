# Tablas, gráficos y diagramas editables

Usa esta guía para slides con evidencia cuantitativa o relaciones que requieran una visualización.

## Tablas

- Mantén como objetos nativos las tablas pedidas. Conserva encabezados, filas, columnas, periodos, unidades y precisión.
- Ajusta el ancho de las columnas, altura de las filas y relleno de las celdas al texto real. Mantén alineación y orden visual de la plantilla.
- Calcula cada total una sola vez y reutilízalo en título, tabla, notas y narración. Declara sumas requeridas en `requirements.arithmetic_contracts`; el checker solo impone estos contratos explícitos.
- El chequeo de sumas no valida por sí solo ratios, subtotales con distintas unidades, redondeo contable, números localizados ni coherencia con afirmaciones del texto. Verifica eso desde la fuente.
- No conviertas una lista breve en tabla sin que la comparación tabular ayude a la audiencia.

## Gráficos

- Conserva categorías, orden de series, unidades, fechas, signo y precisión. Escoge el tipo de gráfico para la pregunta de la audiencia.
- Usa el título y etiquetas nativos del chart. Evita repetir título o etiquetas en cuadros de texto y no dejes el placeholder “Chart Title”.
- Configura formato del eje y de etiquetas en la presentación, no asumas que el formato de Excel sobreviva a la importación.
- Un porcentaje debe corresponder al valor numérico correcto. Por ejemplo, con formato `0%`, 31% se representa como `0.31`.
- Para series apiladas, revisa signos y magnitudes. Nunca conviertas negativos a positivos en la fuente sin rotular la representación con precisión.
- Los charts de `python-pptx` son nativos y editables. Esta implementación permite los 29 tipos que comprobó como serializables el writer público de `python-pptx` 1.0.2: barras y columnas agrupadas/apiladas/100%, líneas lisas o con marcadores y variantes apiladas, áreas y variantes apiladas/100%, pastel y anillo (también explotados), radar, dispersión XY (líneas rectas o suavizadas, con o sin marcadores) y burbujas (incluido el efecto 3D). El enum `pie_of_pie` existe en la biblioteca, pero su writer no lo serializa en esa versión; por eso no se ofrece.
- Se admiten colores por serie o punto, estilos de chart, títulos, leyendas, formatos numéricos, límites/unidades/ejes y etiquetas configurables en charts categóricos. `python-pptx` no expone etiquetas de datos editables para XY/bubble; el compilador rechaza explícitamente esa combinación. No replica todos los formatos especiales de Excel, fórmulas externas o comportamientos de PowerPoint. Explica cualquier limitación que afecte al resultado.
- Comprueba visualmente que etiquetas, escalas, leyendas y unidades corresponden a los datos.

## Diagramas y assets

- Usa formas y conectores nativos para diagramas explícitamente pedidos o que expliquen el argumento. Evita crear gráficos decorativos con formas vectoriales.
- Alinea cada etiqueta con el nodo que describe. Mantén conectores fuera de las áreas de texto; prefiere recorridos rectos y simples.
- Mantén imágenes aportadas por el usuario sin alteración si así se pide. No uses una imagen de un evento como si fuera evidencia fotográfica cuando es una ilustración generada.
