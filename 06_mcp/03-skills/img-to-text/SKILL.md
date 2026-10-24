---
name: img-to-text
description: >
  Transcribe a un .md el texto de una o varias imágenes (capturas de pantalla,
  fotos de documentos, páginas escaneadas, diapositivas, pizarras), palabra por
  palabra, sin inventar ni corregir nada y con un formato Markdown parecido al
  de la imagen. Actívala cuando pidan pasar imágenes a texto, hacer OCR o
  transcribir lo que pone en una imagen.
---

# Img to Text

Entrada: **una o varias imágenes** (o una carpeta). Salida: **un `.md` con exactamente el texto de las imágenes**, en orden. Tú lees las imágenes (visión) y transcribes; un OCR local independiente (RapidOCR) actúa de segundo lector para detectar palabras mal leídas, inventadas u omitidas. Ejecuta los scripts desde esta carpeta, con un venv (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`; propónselo al usuario, no lo instales sin avisar). La primera ejecución del OCR descarga sus modelos (unas decenas de MB); después funciona sin red.

## Reglas que mandan sobre todo lo demás

1. **Mismas palabras, mismo texto.** Copia lo que está escrito: misma ortografía (también las faltas), acentos, mayúsculas, puntuación, cifras, símbolos, abreviaturas e idioma. No corrijas, no traduzcas, no resumas, no completes, no «mejores».
2. **No inventes nada.** Si no se lee, escribe `[ilegible]`; si dudas, `[dudoso: lo que crees leer]`. Nunca rellenes con lo que «debería» poner.
3. **El formato sí lo decides tú**, pero parecido al de la imagen: títulos, listas, tablas, negrita, cursiva, código, citas, columnas. El formato no puede añadir ni quitar palabras.

Lee `references/transcription_rules.md` antes de transcribir.

## Flujo de trabajo

1. **Recibe las imágenes.** Rutas de ficheros o una carpeta. Si la imagen solo está pegada en el chat y no hay fichero, puedes transcribirla viéndola, pero **no podrás pasar el OCR de verificación**: dilo y pide la ruta si el usuario quiere esa comprobación.
2. **Prepara.** `.venv/bin/python scripts/prepare_images.py /ruta/imagen.png [otra.png …] --output-dir /ruta/trabajo` (o una carpeta). Corrige la orientación (EXIF y, con el OCR, fotos giradas 90°/180°/270°: lo avisa con «girada N°»; comprueba con Read que quedó derecha o fuerza `--rotate`), amplía lo muy pequeño, y **trocea las imágenes altas** (si no, la herramienta de visión las reduce y el texto pequeño se pierde). Con una carpeta ordena por número (`pag_2` antes que `pag_10`); con varias rutas respeta el orden dado.
   - Código de salida `3` (**orden ambiguo**): **para y pregunta al usuario** (nombres sin números, series mezcladas…). Con su respuesta usa `--files-from` (un nombre por línea).
   - Si el texto es desvaído o hay fondos grises, añade `--enhance`.
3. **Transcribe.** Mira con `Read` **cada trozo** que lista el script, en orden, y escribe `<trabajo>/partes/NN_<nombre-imagen>.md` (NN con dos dígitos, como en `lectura.json`). En imágenes con varios trozos el solape (120 px) repite líneas: transcríbelas una sola vez.
4. **Une.** `.venv/bin/python scripts/join_parts.py /ruta/trabajo` → `transcripcion.md` (separa las imágenes con `---` y un comentario `<!-- imagen N: nombre -->`, invisibles y sin palabras nuevas).
5. **Verifica con el segundo lector.** `.venv/bin/python scripts/check_transcription.py /ruta/trabajo/transcripcion.md --work-dir /ruta/trabajo`. Para **cada aviso** (`INVENTADO?/MAL LEÍDO?`, `OMITIDO?`, `REVISAR`) mira la zona ampliada (`scripts/zoom_image.py <trozo> --box x0,y0,x1,y1`, con `Read` sobre la imagen resultante), decide qué pone **realmente** y corrige solo si la imagen lo confirma: el OCR también se equivoca. Vuelve a unir y a verificar.
6. **Relectura final.** Compara a ojo cada trozo con su parte del `.md`: palabra por palabra, cifras, signos, orden. El script no detecta todo (ver límites).
7. **Entrega.** Indica la ruta de `transcripcion.md`, cuántas imágenes y en qué orden, los marcadores `[ilegible]`/`[dudoso: …]` que queden y qué no pudiste verificar. Si el usuario pide el `.md` en otro sitio, cópialo allí.

## Salida

```
trabajo/
├── transcripcion.md       # el resultado
├── partes/NN_<imagen>.md  # una parte por imagen (las escribes tú)
├── tiles/                 # trozos de imagen que se leen con Read
├── lectura.json           # orden, tamaños y trozos
└── ocr.json               # caché del OCR
```

Ver `examples/` (una página de ejemplo y su transcripción).

## Límites deliberados

- La visión puede confundir letras parecidas (`l`/`1`/`I`, `0`/`O`, `rn`/`m`), sobre todo en texto pequeño, borroso o manuscrito. Por eso hay segundo lector y zoom; aun así, **no es una garantía**.
- `check_transcription.py` es una heurística por palabras: no detecta cambios de orden, signos de puntuación mal puestos, mayúsculas/acentos distintos (los ignora al comparar) ni palabras cortas (<4 letras) mal leídas salvo que no existan en el OCR.
- RapidOCR lee bien alfabeto latino y chino; en otros alfabetos o en manuscrito su verificación es poco fiable.
- No describe imágenes: solo transcribe texto (incluido el de logos, gráficos y diagramas). Las fotos o dibujos sin texto se ignoran.
- Solo `.png .jpg .jpeg .webp .bmp .tif .tiff .gif`. Para PDF, renderiza antes las páginas a imagen (p. ej. `pdftoppm -r 100 -png`) o extrae su texto directamente.
