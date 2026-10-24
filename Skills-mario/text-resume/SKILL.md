---
name: text-resume
description: >
  Lee a fondo un fichero de texto o una carpeta de ficheros de texto ordenados
  (.txt/.md: transcripciones, actas, artículos, capítulos) y produce, sin
  inventar nada, un .md que explica de qué trata, un resumen extenso con todo
  lo importante y un PDF idéntico al resumen. Actívala cuando pidan resumir,
  analizar o explicar de qué va un texto largo, o resumir una transcripción
  (p. ej. la generada por audio-decoder).
---

# Text Resume

Entrada: **un fichero de texto o un directorio de ficheros de texto ordenados**. Salida, en este orden: (1) `descripcion.md` — de qué trata el texto; (2) `resumen.md` — resumen extenso; (3) `resumen.pdf` — con exactamente la misma información que `resumen.md`.

La inteligencia del trabajo (leer, entender, redactar) la pones tú; los scripts de esta carpeta preparan la lectura, comprueban la fidelidad y generan el PDF. Ejecuta los scripts desde esta carpeta. `collect_texts.py` solo usa la biblioteca estándar; `md_to_pdf.py` y `check_summary.py` necesitan el entorno compartido de la raíz del repo (si no existe: `python3 ../scripts/setup_env.py`; define `PY="$(git rev-parse --show-toplevel)/.venv/bin/python"` y úsalo como `$PY`, no con `../` en la ruta, que provoca avisos; propónselo al usuario, no lo instales sin avisar).

## Reglas que mandan sobre todo lo demás

1. **No inventes nada.** Solo lo que dice el texto: sin conocimiento externo, sin suposiciones, sin opiniones. Si algo no queda claro, escríbelo como «no queda claro» en vez de rellenarlo.
2. **No te comas lo importante.** Se prefiere un resumen extenso a uno que omita cosas. Ante la duda, incluye.
3. **Lee todo antes de escribir.** Nada de ojear, muestrear ni resumir desde el principio y el final. No redactes ningún fichero hasta haber leído y entendido el texto completo.

Lee `references/writing_rules.md` antes de redactar.

## Flujo de trabajo

1. **Prepara la lectura.** `python3 scripts/collect_texts.py /ruta/entrada --output-dir /ruta/resumen`. (Carpeta de salida por defecto: `resumen/` junto a la entrada, salvo que el usuario indique otra.) Ordena los ficheros por número (`parte_2` antes que `parte_10`), crea `texto_trabajo.txt` (todo el texto en orden, con líneas cortas para que `Read` no las trunque) y muestra el **plan de lectura** por trozos.
   - Código de salida `3` (**orden ambiguo**): **para y pregunta al usuario antes de empezar.** Con su respuesta escribe un fichero con un nombre por línea y vuelve a ejecutar con `--files-from`. Un `AVISO` de huecos en la numeración (falta un fichero) no bloquea, pero díselo al usuario.
2. **Lee TODO el texto.** Con `Read` sobre `texto_trabajo.txt` (nunca sobre el original), trozo a trozo y en orden, usando `offset`/`limit` del plan. No te saltes ningún trozo. Tras cada trozo apunta en `notas_de_lectura.md` (en la carpeta de salida) lo que contiene: temas, hechos, cifras, fechas, nombres, decisiones, advertencias, citas literales clave y dudas. Marca cada trozo como leído. Si el texto es corto (≤ ~2500 palabras) basta con una pasada y notas breves. Protocolo completo en `references/workflow.md`.
3. **Compruébate que lo has entendido.** Cuando termines de leer, escribe al final de las notas una «Comprensión global»: de qué trata, quién interviene, cómo se estructura, qué se concluye o decide, y qué queda abierto. Si algo importante es ambiguo y no se puede resolver con el texto, pregunta al usuario; si no, déjalo como «no queda claro».
4. **Crea `descripcion.md`** (de qué trata el texto) con la plantilla `assets/descripcion_template.md`: tipo de texto, participantes, tema central, temas en orden, lo más importante y lo que el texto no aclara.
5. **Crea `resumen.md`** con `assets/resumen_template.md`: resumen **extenso**, en el orden del texto, con todo lo importante (decisiones, cifras, fechas, nombres, plazos, condiciones, advertencias, razones), más tablas de datos concretos y de compromisos/pendientes si procede. Mismo idioma que el texto.
6. **Verifica la fidelidad.** `$PY scripts/check_summary.py resumen/resumen.md --source /ruta/entrada` (y lo mismo con `descripcion.md`). Cada `INVENTADO?` hay que contrastarlo con el texto y corregirlo o justificarlo; cada `OMITIDO?` hay que valorarlo y, si es importante, añadirlo. Después relee tus ficheros contra `texto_trabajo.txt` por si el script no atrapa algo (ver límites). Repite hasta que no queden dudas.
7. **Crea el PDF.** Solo cuando `resumen.md` esté aprobado: `$PY scripts/md_to_pdf.py resumen/resumen.md` y comprueba `$PY scripts/check_summary.py resumen/resumen.md --pdf resumen/resumen.pdf`: debe decir que el PDF coincide palabra por palabra. Si editas el `.md`, regenera el PDF. Mira el PDF (p. ej. con `Read` sobre el PDF o una imagen) por si hay un problema de maquetación.
8. **Entrega.** Indica las rutas de `descripcion.md`, `resumen.md` y `resumen.pdf`, los ficheros leídos y su orden, y qué no pudiste verificar o qué quedó «no claro». Si el texto contiene datos personales o sensibles, recuerda que todo se procesó en local y que los ficheros contienen esa información.

## Salida

```
resumen/
├── descripcion.md          # de qué trata el texto
├── resumen.md              # resumen extenso (fuente del PDF)
├── resumen.pdf             # mismo contenido que resumen.md
├── notas_de_lectura.md     # notas de trabajo y comprensión global
├── texto_trabajo.txt       # copia de trabajo ordenada (no editar)
└── lectura.json            # orden, palabras y plan de lectura
```

Ver `examples/` (entrada ficticia de 3 ficheros, `descripcion.example.md` y `resumen.example.md`).

## Límites deliberados

- Solo `.txt` y `.md`. Para PDF/Word/audio conviértelos antes (p. ej. audio → `audio-decoder`).
- `check_summary.py` es una heurística: detecta cifras, nombres propios y citas del resumen que no están en el texto, y cifras/nombres frecuentes del texto que faltan en el resumen. **No detecta** nombres al inicio de una frase, errores de significado, atribuciones cambiadas (quién dijo qué), cifras escritas con letras ni una omisión de ideas sin cifras ni nombres. La relectura manual es obligatoria.
- Los avisos `OMITIDO?` en `descripcion.md` son normales (no es exhaustiva); aplícalos sobre todo a `resumen.md`.
- Las transcripciones automáticas tienen errores (nombres, jerga). No los «corrijas» en silencio: señálalos como dudosos.
- `md_to_pdf.py` soporta títulos, párrafos, listas, tablas, citas y código, no imágenes ni HTML. Con caracteres fuera de cp1252 usa DejaVu Sans, sin cursiva real, y para los que DejaVu no tiene (CJK…) una fuente de reserva; si no hay ninguna, falla en vez de perder texto (ver `references/errores_conocidos.md`).
