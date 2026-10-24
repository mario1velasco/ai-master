# Plantillas y edición de PPTX existentes

Lee esta guía cuando el usuario adjunte un PPTX para editarlo o pida igualar una referencia.

## Determina el objetivo del archivo

Pregunta qué papel cumple el archivo solo si no se puede inferir: edición de contenido, réplica del diseño, inspiración visual o fuente de datos/imágenes. Si el usuario aporta un PPTX solo como contenido fuente, no copies su apariencia por defecto.

## Inspecciona antes de compilar

Usa `scripts/inspect_presentation.py fuente.pptx --output inspeccion.json`. Revisa dimensiones reales, número de slides, nombres de layouts, placeholders, posiciones, tamaños, textos, fuentes, imágenes, tablas y charts. Si una referencia es imagen/PDF, examínala visualmente. No asumas 16:9.

## Modos que soporta el compilador

- **Añadir slides a una plantilla:** `template.path` carga el PPTX existente, conserva sus slides y masters, y añade nuevas slides usando `layout` (nombre) o `layout_index` (índice cero-based del catálogo de esa plantilla). El número final incluye las slides originales.
- **Rellenar placeholders existentes:** usa `target_slide` con número one-based y `placeholders` con sus índices exactos de PowerPoint. Los strings sustituyen el texto del placeholder y conservan en lo posible su estilo heredado. Usa `scripts/inspect_presentation.py` para descubrir índices.
- **Editar formas con nombre:** `replace_shapes` sustituye texto en formas nombradas de `target_slide`. No añade, elimina ni mueve formas existentes.
- **Añadir elementos editables:** `elements` posiciona cuadros, imágenes, tablas, charts, formas y conectores sobre una slide nueva o una slide existente especificada. Para una edición existente, declara las colisiones intencionales en `requirements.allowed_overlaps`.

Trabaja siempre desde una copia de la fuente y exporta a una ruta nueva. La biblioteca no ofrece una operación pública para clonar, eliminar o reordenar slides, cambiar masters con fidelidad total ni conservar cada objeto avanzado. El checker compara las dimensiones, layouts y huellas visibles de las slides fuente; no certifica que PowerPoint las renderice idénticas.

## Verifica el resultado

Ejecuta `scripts/check_template_fidelity.py fuente.pptx resultado.pptx`. Si se rellenaron slides existentes, pasa `--allow-changed-slide N` por cada slide modificada. Revisa visualmente fuente y resultado lado a lado en la aplicación destino. No afirmes fidelidad visual basándote solo en un import correcto o en una firma estructural.
