# Mapa de portabilidad desde la skill original

La fuente de comparación es `presentations-skill-export/presentations` dentro del ZIP proporcionado. El objetivo es portar la lógica útil de la skill al API público `python-pptx`; no reproducir sus dependencias ni fingir compatibilidad con funciones que no tienen reemplazo.

## Instrucciones y referencias

| Área original | Adaptación abierta | Cobertura |
| --- | --- | --- |
| `SKILL.md`, orden de trabajo y calidad editorial | `SKILL.md`, `design_rules.md` y `writing_quality.md` | Portado y resumido |
| Selección de plantilla con selector de artifacts | Uso de una plantilla local aportada, o elección manual de theme/layout | Parcial; no hay picker ni catálogo MCP |
| Diseño de portada | `design_rules.md` y `template_workflow.md` | Portado |
| Edición/seguimiento de plantilla | `template_workflow.md`, `compile_deck.py`, `inspect_presentation.py`, `check_template_fidelity.py` | Parcial; se pueden editar textos de placeholders, agregar slides con layouts y comprobar dimensiones/estructura básica |
| Guía de finanzas | `finance.md`, contratos aritméticos y gráficos nativos | Portado y adaptado |
| Guía de tablas y gráficos | `data_visuals.md`, compilador y verificadores | Portado para objetos nativos comunes |
| Formato de bullets | Placeholders conservan su estilo; cuadros creados por el compilador usan `•` editable | Parcial; no se modifica XML para imitar la API privada |
| Google Slides | Se explica el límite; salida local PPTX para importación manual | Sin conector ni upload automático |

## Implementación y herramientas

| Original | Adaptación abierta | Razón / límite |
| --- | --- | --- |
| Runtime `CODEX_PRIMARY_RUNTIME_*`, binarios internos, Node y `@oai/artifact-tool` | Python 3 y paquete público `python-pptx` | Eliminado por requisito de portabilidad |
| Manuales `artifact_tool_docs/` | `python_pptx_api.md` y enlaces oficiales; Context7 bajo demanda | El API y los ejemplos originales no aplican a python-pptx |
| `artifact_tool_utils.mjs` | `scripts/compile_deck.py` y `scripts/pptx_components.py`, con checks escritos con API pública | Portados los flujos de tipografía, columnas, objetos, conteo y validación aplicables |
| Inspector y finalizer de integridad/layout | `check_overflow.py`, `inspect_presentation.py`, validadores especializados | QA geométrico y estructural local; no valida el render del programa destino |
| Gate de aritmética de tablas | `check_table_arithmetic.py` | Solo contratos de sumas explícitos; no infiere que un subtotal sea una suma |
| Gates de chart/title y referencias de datos | Comprobaciones de títulos, series y valores expuestos por python-pptx | Parcial; no verifica todas las fórmulas, referencias de celdas ni el comportamiento entre aplicaciones |
| Checker de fidelidad de plantilla | `check_template_fidelity.py` | Compara dimensiones, layouts y formas de las diapositivas fuente que se deben preservar; no prueba equivalencia visual |
| Render de slides, contact sheet y rasterización SVG/PDF | Inspección manual en PowerPoint/visor | No hay renderizador en python-pptx. Rasterizar SVG/PDF exigiría otra dependencia |
| Herramientas de imagen con Pillow/Node | `add_picture()` para formatos aceptados por python-pptx | Se elimina el pipeline adicional; convertir SVG/PDF queda fuera del núcleo portable |
| Comentarios, SmartArt, animación y transiciones | Se documentan como no soportados por API pública completa | No se editan partes OOXML privadas |

## Consecuencia práctica

La nueva skill cubre el flujo habitual de decks editables con texto, tablas, charts, imágenes, notas y layouts, además del QA determinista posible sin Office. No ofrece paridad con todas las funciones privadas, conectores de producto o inspección visual automatizada de la skill original. Cada límite debe comunicarse cuando afecte al entregable.
