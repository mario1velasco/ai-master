# Errores conocidos

Fallos que ya han ocurrido al usar esta skill, su causa y cómo se evitan. Añade una entrada cada vez que algo falle.

## md_to_pdf.py perdía en silencio caracteres sin glifo (2026-10-09)
- **Síntoma:** `check_summary.py --pdf` fallaba con `delete: .md «東京» ↔ PDF «»`: el PDF no mostraba texto en chino/japonés/coreano (o emojis) aunque estaba en el `.md`.
- **Causa:** con caracteres fuera de cp1252 se usaba solo DejaVu Sans, que no tiene glifos CJK; reportlab escribe el carácter sin glifo y el extractor no lo recupera (se ve como un hueco).
- **Solución:** `scripts/md_to_pdf.py` comprueba la cobertura de cada carácter; los que la fuente principal no tiene se escriben con una fuente TrueType de reserva encontrada con `fc-list :charset=…` (función `find_fallback`); si ninguna los tiene, el script termina con error y lista los caracteres. Lo mismo en bloques de código (Courier). Detectado al crear la skill `any-to-any`, que usa una copia del mismo script.
- **Prevención:** no ignores un FALLO de `check_summary.py --pdf`; si `md_to_pdf.py` dice que faltan fuentes, instala una con esos caracteres (`fonts-noto`, `fonts-droid-fallback`) o pasa `--font`. reportlab solo lee TrueType (`.ttf`), no `.otf`/`.ttc` CFF.
