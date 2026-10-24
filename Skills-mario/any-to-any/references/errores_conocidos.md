# Errores conocidos

Fallos que ya han ocurrido al usar esta skill, su causa y cómo se evitan. Añade una entrada cada vez que algo falle (formato en el `CLAUDE.md` de la raíz). Si el fallo nace en una skill hermana, documéntalo allí y enlázalo aquí.

## markitdown cambia valores de Excel (2026-10-09)
- **Síntoma:** en la extracción de un `.xlsx` aparecían `10.0` donde la celda tenía `10` y `NaN` en celdas vacías.
- **Causa:** markitdown convierte las hojas con pandas, que pasa las columnas numéricas a float y marca los vacíos como NaN.
- **Solución:** `scripts/convert_docs.py` usa un conversor propio para hojas (`sheet_xlsx`, `sheet_xls`, `sheet_csv`) en vez de markitdown.
- **Prevención:** las hojas de cálculo y CSV son tipo `sheet` en `inventory.py`; no las pases por markitdown.

## markitdown añade rótulos que no están en el original (2026-10-09)
- **Síntoma:** `### Notes:` en las notas del orador de PowerPoint, nombres de fichero de imagen como texto (`![pagina_2.png](Picture3.jpg)`) y filas de cabecera vacías en tablas de Word.
- **Causa:** son marcas de markitdown, no contenido del documento; en PDF/DOCX se verían como texto.
- **Solución:** `clean_markitdown` y `drop_empty_table_headers` en `scripts/convert_docs.py` los pasan a comentarios invisibles o los corrigen.
- **Prevención:** si aparece un rótulo nuevo de markitdown, añádelo a `clean_markitdown` y a `references/formatos_entrada.md`.

## El PDF perdía caracteres CJK en silencio (2026-10-09)
- **Síntoma:** `check_output.py` fallaba con `delete: .md «東京» ↔ x.pdf «»`.
- **Causa:** la fuente de reserva para Unicode (DejaVu Sans) no tiene glifos CJK. El fallo venía de `text-resume/scripts/md_to_pdf.py`, del que este script es copia: ver `../../text-resume/references/errores_conocidos.md`.
- **Solución:** `scripts/md_to_pdf.py` busca una fuente TrueType de reserva con `fc-list` por carácter y falla si no hay ninguna (arreglado también en text-resume).
- **Prevención:** no ignores un FALLO de `check_output.py`; si `md_to_pdf.py` dice que faltan fuentes, instala una que tenga esos caracteres.

## La transcripción de audio fallaba con «metadata_errors» (2026-10-09)
- **Síntoma:** `process_audio.py` → `error: falló la transcripción` con `TypeError: open() got an unexpected keyword argument 'metadata_errors'`.
- **Causa:** `av 19` incompatible con `faster-whisper 1.2.1` (skill hermana audio-decoder): ver `../../audio-decoder/references/errores_conocidos.md`.
- **Solución:** `av==18.1.0` fijado en los requirements; `setup_env.py` ahora reinstala si las versiones no coinciden con las fijadas.
- **Prevención:** ejecuta `python3 ../scripts/setup_env.py` tras actualizar el repo.
