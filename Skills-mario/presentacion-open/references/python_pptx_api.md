# API público de python-pptx

La implementación se basa en la documentación oficial de `python-pptx` consultada con Context7 usando `/scanny/python-pptx`, y fue comprobada en Python 3.13 con `python-pptx` 1.0.2. Context7 se usa para verificar documentación al diseñar o extender el compilador; no se necesita en ejecución.

## Fuentes oficiales

- [Quickstart](https://python-pptx.readthedocs.io/en/latest/user/quickstart.html)
- [Text](https://python-pptx.readthedocs.io/en/latest/user/text.html)
- [Tables](https://python-pptx.readthedocs.io/en/latest/user/table.html)
- [Charts](https://python-pptx.readthedocs.io/en/latest/user/charts.html)
- [Presentation API](https://python-pptx.readthedocs.io/en/latest/api/presentation.html)

Para una extensión avanzada, resuelve `python-pptx` en Context7 y consulta un concepto por llamada: cuadros de texto y runs, tablas, charts, layouts/plantillas o imágenes. Si el MCP no está disponible, abre la documentación oficial. No inventes métodos a partir de documentación de otras bibliotecas.

## Unidades y texto

- Las coordenadas y dimensiones de `slide.shapes.add_textbox()` y `add_picture()` usan unidades EMU; construye las entradas con `Inches(x)`, `Inches(y)`, `Inches(width)`, `Inches(height)`.
- Los tamaños tipográficos son puntos: asigna `run.font.size = Pt(size_pt)`. Para colores, asigna `run.font.color.rgb = RGBColor(...)`; para familia, `run.font.name = "Roboto"` u otra familia solicitada.
- El margen interno pertenece a `shape.text_frame`: `margin_left`, `margin_right`, `margin_top`, `margin_bottom`. Exprésalo en `Inches`. `word_wrap` es booleano. Desactiva el autoajuste si quieres conservar el tamaño tipográfico previsto.
- Representa párrafos y saltos intencionales mediante los métodos de `TextFrame` y sus párrafos. No coloques texto en varias formas para simular un único bloque con estilos mixtos. Runs mantienen texto y formatos editables.

## Tablas

Usa `slide.shapes.add_table(rows, cols, left, top, width, height).table`. Ajusta `table.columns[i].width = Inches(...)` y `table.rows[i].height = Inches(...)`. Asigna texto y formato a cada celda. El compilador usa estas propiedades públicas para conservar tablas editables.

## Charts

Usa `CategoryChartData` para series con categorías y `XyChartData` para dispersión. Crea la forma con `slide.shapes.add_chart(chart_type, x, y, cx, cy, data).chart`. Títulos, ejes, leyendas y etiquetas se asignan desde la instancia de chart. Conserva valores, unidades, orden, categorías y signos originales.

El compilador ofrece los 29 tipos que el writer público de `python-pptx` 1.0.2 pudo serializar en la matriz de compatibilidad local; `pie_of_pie` fue excluido porque la biblioteca falla al escribirlo. No garantiza fidelidad de cada formato especial de Excel, workbook externo, error bars, múltiples niveles de categorías, etiquetas complejas o compatibilidad idéntica entre PowerPoint y otros lectores. En particular, el API público no permite configurar las etiquetas de datos de charts XY/bubble. Inspecciona el archivo final en su aplicación destino cuando esos detalles sean esenciales.

## Imágenes, layouts y notas

- Inserta imágenes con `slide.shapes.add_picture()`. El compilador soporta BMP, GIF, JPEG, PNG, TIFF y WMF aceptados por la versión usada. SVG y PDF requieren rasterización externa y no forman parte de las dependencias.
- Abre una plantilla con `Presentation(path)`, selecciona `presentation.slide_layouts` y crea nuevas slides con `slides.add_slide(layout)`. Edita placeholders usando el índice público de placeholder. Guarda siempre en otra ruta.
- Las notas se escriben en `slide.notes_slide.notes_text_frame` cuando el layout de notas ofrece el placeholder correspondiente. Fuentes y notas se guardan ahí, salvo que deban verse en la slide.

## Regla de implementación

Usa únicamente nombres y propiedades documentados del API público. No dependas de `.element`, `._sp`, `_sldIdLst` u otros miembros internos. Si una operación requiere esos detalles (eliminar o reordenar slides, clonar masters, manipular comentarios/animaciones o reparar referencias OOXML), documenta la limitación y no la simules como una operación verificada.
