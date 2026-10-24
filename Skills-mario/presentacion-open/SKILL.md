---
name: presentations-open
description: >
  Crea y valida presentaciones PowerPoint (.pptx) editables usando python-pptx
  y un validador geométrico de márgenes. Actívala para peticiones de diapositivas,
  decks y presentaciones corporativas sin dependencias propietarias.
---

# Presentations Open

Usa el compilador y las herramientas de esta carpeta para crear y revisar PPTX con Python 3 y la API pública de `python-pptx`. Usa el venv compartido de la raíz del repo (`PY="$(git rev-parse --show-toplevel)/.venv/bin/python"`, se crea con `python3 ../scripts/setup_env.py`; ejecuta los scripts con `$PY`); no instales nada automáticamente. El runtime usa `python-pptx` y la biblioteca estándar. No compruebes variables `CODEX_PRIMARY_RUNTIME_*`, no uses `dependencies/bin/override` ni `@oai/artifact-tool`.

## Flujo de trabajo

1. **Ingesta y normaliza.** Extrae del encargo el objetivo, audiencia, número total de slides, contenido, datos, fuentes, instrucciones de marca y archivos aportados. Normalízalos a `deck.json` según `references/deck_schema.md`; no inventes los hechos faltantes.
2. **Verifica las reglas de diseño.** Aplica `references/design_rules.md` y `references/writing_quality.md`. Para una plantilla o un PPTX existente, lee `references/template_workflow.md`; para gráficos o tablas, `references/data_visuals.md`; para un deck financiero, `references/finance.md`; para Google Slides, `references/google_slides.md`. Confirma el límite por contenedor, la densidad y el orden de lectura antes de compilar.
3. **Compila.** Ejecuta desde esta carpeta `$PY scripts/compile_deck.py /ruta/deck.json --output /ruta/out/presentation.pptx`. Las rutas de imágenes se resuelven desde el directorio del JSON. El compilador crea tablas y gráficos nativos editables y puede trabajar sobre una plantilla PPTX.
4. **Ejecuta el bucle de QA.** Ejecuta `$PY scripts/check_overflow.py out/presentation.pptx --spec deck.json` y corrige márgenes, solapamientos, texto y requisitos hasta que pase. Añade `$PY scripts/check_package_integrity.py out/presentation.pptx`; cuando corresponda, ejecuta `$PY scripts/check_table_arithmetic.py out/presentation.pptx --spec deck.json` y `$PY scripts/check_template_fidelity.py template.pptx out/presentation.pptx --allow-changed-slide N` para cada slide de plantilla editada. Usa `scripts/inspect_presentation.py` para localizar problemas y recompila después de cada corrección.
5. **Consulta Context7 para componentes avanzados.** Si necesitas un componente de `python-pptx` que no esté cubierto por `references/python_pptx_api.md`, resuelve `python-pptx` en Context7 y consulta la documentación oficial antes de codificar. El ID usado en la auditoría fue `/scanny/python-pptx`. Context7 solo aporta documentación: no es una dependencia de ejecución.
6. **Revisa visualmente.** Inspecciona cada diapositiva a tamaño de lectura en PowerPoint o en el visor disponible. `python-pptx` no renderiza diapositivas. Los validadores geométricos no demuestran que los saltos de línea, el ajuste tipográfico, los recortes o la apariencia sean correctos.
7. **Entrega.** Guarda en un archivo nuevo y no sobrescribas la fuente. Indica limitaciones relevantes, como contenido que no se pudo validar visualmente o una función que el API público no ofrece.

Lee `references/porting_matrix.md` para saber qué funciones de la skill original tienen reemplazo directo, parcial o ninguno. Lee `references/qa_delivery.md` para el flujo completo de validación y límites.

## Capacidades implementadas

- Texto editable con párrafos, runs tipográficos, enlaces, alineación, márgenes y saltos de párrafo; los bloques automáticos cortos conservan sus estilos enriquecidos.
- Distribución automática o explícita en una a tres columnas, con separación contigua que conserva el orden de lectura.
- Tablas nativas con anchos de columna, alturas de fila, celdas combinadas, estilo de cabecera y bandas.
- Gráficos nativos editables: variantes de barras, columnas, líneas, áreas, pastel, anillo, radar, dispersión XY y burbujas; configura series, leyendas, etiquetas compatibles, colores y ejes.
- Imágenes locales con ajuste `contain`, `cover` o `stretch`.
- Formas y conectores editables para diagramas pedidos o informativos, con posiciones en pulgadas.
- Notas del orador, fuentes, propiedades del documento, layouts y placeholders de plantillas.
- QA de márgenes, colisiones, límites de texto, slides requeridas, fuentes declaradas, tablas y fidelidad básica de plantilla.

## Límites deliberados

- El paquete crea o edita archivos PPTX locales. No conecta a Google Drive ni convierte/importa a Google Slides.
- `python-pptx` no renderiza, no genera animaciones o transiciones y no ofrece una API pública completa para comentarios, SmartArt, edición avanzada de masters o todos los efectos visuales de PowerPoint. Consulta `references/porting_matrix.md` antes de prometer esas funciones.
- La API pública no ofrece un control de viñetas tipográficas completo para un cuadro de texto vacío. Conserva las viñetas heredadas de placeholders de plantilla; el layout automático usa el carácter editable `•` en cuadros independientes. La edición de etiquetas de datos no está disponible en esta implementación para charts XY/bubble.
- No crea dibujos decorativos como sustituto de imágenes. Usa las formas para diagramas editables que ayuden a explicar una relación. No se instalan dependencias de renderizado, imágenes o Office.
- El límite de 180 caracteres por contenedor y la partición automática en columnas son convenciones de este compilador, no reglas literales de la skill original.
