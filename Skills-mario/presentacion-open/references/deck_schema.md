# Esquema de `deck.json`

El compilador acepta `version` 1 (compatibilidad con el esquema inicial) y `version` 2 (elementos, plantilla y QA ampliados). Las dimensiones de objetos están en pulgadas y los tamaños tipográficos en puntos.

## Raíz

- `metadata`: `title`, `subject`, `author`, `keywords`, `comments` del documento.
- `template`: ruta PPTX o `{ "path": "..." }`; relativa al JSON.
- `slide_size`: `{ "width_in": 13.333, "height_in": 7.5 }`; si hay template, debe coincidir con su tamaño.
- `theme`: `font_name`, colores hex RGB, `title_pt`, `body_pt`, `cover_title_pt`, `safe_margin_inches`, `chart_colors`.
- `font_policy`: `{ "basis": "design|user_request|reference", "families": ["Roboto"] }`. Documenta de dónde proviene la fuente; no comprueba si está instalada ni la incrusta.
- `requirements`: `total_slides`, `required_native_table_slides`, `required_native_chart_slides`, `allowed_overlaps` y `arithmetic_contracts`.
- `slides`: lista no vacía de objetos.

## Slide

- `kind`: `cover`, `content` o `existing`. `existing` requiere `target_slide`.
- `target_slide`: índice one-based de slide en la plantilla para editar.
- `layout`: nombre exacto o índice cero-based del layout al crear una slide nueva. Se conserva el layout original. En versión 1 los valores `auto`, `single`, `two_columns` y `three_columns` siguen funcionando como alias de `layout_mode`.
- `title`, `subtitle`, `notes`, `sources`.
- `placeholders`: mapa de índice público de placeholder a string o contenido enriquecido. Una cadena conserva el formato del placeholder.
- `replace_shapes`: mapa de nombre exacto de forma a texto; solo se pueden sustituir formas que tengan un cuadro de texto.
- Layout automático: `items`, `columns`, `bullet`, `layout_mode` (`auto`, `single`, `two_columns`, `three_columns`; `layout` conserva el alias legacy), `image`, `table`, `chart`. Un bloque de `items`/`columns` puede ser una cadena o contenido enriquecido; el texto enriquecido mantiene sus runs si cabe en 180 caracteres, mientras que las cadenas más largas se dividen en límites de palabra/oración.
- Layout explícito: `elements`, lista de elementos tipados y ordenados por z-order.
- `sources` se guarda en las notas del orador junto con `notes`. Cada fuente visible o nota de fuente debe quedar trazable; no se añade texto de fuente a la diapositiva automáticamente.

## Elementos explícitos

Cada elemento tiene `type`, `name` opcional, `x`, `y`, `width`, `height` donde aplique. Las coordenadas y medidas se expresan en pulgadas; los tamaños de letra y trazos, en puntos.

- `textbox`: `text` string o `{ "paragraphs": [{ "runs": [{ "text": "...", "bold": true, "italic": false, "underline": false, "color": "C8102E", "font_name": "Roboto", "font_size_pt": 18, "hyperlink": "https://..." }], "alignment": "left", "space_before_pt": 0, "space_after_pt": 6, "line_spacing": 1.1, "bullet": false, "level": 0 }] }`; y `style` con `font_name`, `font_size_pt`, `color`, `alignment`, `vertical_anchor` (`top|middle|bottom`), `margins_in` (`left|right|top|bottom`), `word_wrap`.
- `image`: `path` (local, relativo al JSON) y `fit`: `contain`, `cover` o `stretch`.
- `table`: `headers`, `rows`, `header_rows`, `column_widths_in` o `column_weights`, `row_heights_in`, `cell_margins_in`, `header_fill`, `header_color`, `body_color`, `stripe_fill`, `font_name`, `font_size_pt`, `alignment`, `vertical_anchor`, `merges` (rangos `[fila1, columna1, fila2, columna2]` zero-based).
- `chart`: tipos `bar`, `bar_stacked`, `bar_stacked_100`, `column`, `column_stacked`, `column_stacked_100`, `line`, `line_plain`, `line_stacked`, `line_stacked_100`, `line_markers_stacked`, `line_markers_stacked_100`, `area`, `area_stacked`, `area_stacked_100`, `pie`, `pie_exploded`, `doughnut`, `doughnut_exploded`, `radar`, `radar_filled`, `radar_markers`, `scatter`, `scatter_lines`, `scatter_lines_no_markers`, `scatter_smooth`, `scatter_smooth_no_markers`, `bubble` y `bubble_3d`. Usa `categories` y `series` con `name`, `values` y, para series XY/bubble, `x_values`; las series bubble también requieren `bubble_sizes`. Se configuran `title`, `title_pt`, `legend`, `data_labels`, `axes`, `colors`, `style`, `font_size_pt`, `font_color`. Los charts XY/bubble no admiten `data_labels`.
- `shape`: `shape_type` (`rectangle`, `rounded_rectangle`, `ellipse`, `diamond`, `chevron`, flechas y nodos de flowchart; también admite nombres públicos de `MSO_SHAPE`), `fill`, `line_color`, `line_width_pt`, y texto opcional con `text_style`.
- `connector`: `start` y `end` con `x`,`y`, `connector_type` (`straight`, `elbow`, `curve`), color y grosor.

El máximo de 180 caracteres se aplica al texto visible de cada forma y celda, incluidos párrafos y runs. El modo automático divide los bloques largos de `items` y `columns` en límites de oración o palabra; los textos de cuadros explícitos, tablas, títulos y categorías deben caber en ese límite sin división implícita.

El compilador no convierte formas en ilustración decorativa. Usa `elements` cuando un slide mezcla varios tipos de contenido o necesita colocación precisa. Los contenedores de texto respetan siempre el máximo de 180 caracteres. Los bloques largos de `items` se dividen automáticamente en límites de oración o palabra; para otros textos, reescribe o reparte el contenido.

## Ejemplo

```json
{
  "version": 2,
  "metadata": { "title": "Resultados", "author": "Equipo" },
  "theme": { "font_name": "Roboto", "safe_margin_inches": 0.6 },
  "font_policy": { "basis": "user_request", "families": ["Roboto"] },
  "requirements": {
    "total_slides": 2,
    "required_native_chart_slides": [2]
  },
  "slides": [
    { "kind": "cover", "title": "Resultados anuales", "subtitle": "Ejercicio 2026", "notes": "Resumen ejecutivo" },
    {
      "title": "Ingresos por región",
      "chart": {
        "chart_type": "column",
        "categories": ["Norte", "Sur", "Este"],
        "series": [{ "name": "Ingresos (M€)", "values": [12.5, 9.7, 14.2], "number_format": "0.0" }],
        "legend": false,
        "data_labels": { "show_value": true, "position": "outside_end", "number_format": "0.0" },
        "axes": { "value": { "minimum": 0, "major_gridlines": true } }
      },
      "sources": ["Fuente: Informe anual, 2026"]
    }
  ]
}
```

En contratos de aritmética, `slide` y `table` son one-based. Las coordenadas de `inputs` y `result` son `[fila, columna]` zero-based, contando la cabecera cuando está en la tabla. `tolerance` es una cadena decimal no negativa.
