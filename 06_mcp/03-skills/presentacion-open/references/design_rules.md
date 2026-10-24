# Reglas de diseño para presentaciones

Esta guía adapta las pautas visuales y editoriales de la skill Presentations original al flujo con `python-pptx`. Sigue primero el diseño, la plantilla, la marca y las instrucciones expresas del usuario.

## Plantillas y dirección visual

- Si el usuario aporta una plantilla o referencia para imitar, examina dimensiones, composición, tipografía, colores, espaciado, imágenes, recortes y elementos repetidos. Conserva esos rasgos en la medida que permita el flujo abierto.
- Si un archivo se aporta solo como fuente de datos o contenido, no supongas que el usuario quiere copiar su diseño.
- El compilador puede abrir un PPTX, rellenar placeholders indicados, agregar slides con layouts de esa presentación y añadir objetos editables. No elimina ni clona slides. Si el trabajo depende de conservar una estructura que el API público no puede modificar, dilo en lugar de afirmar que la plantilla quedó preservada.
- Sin dirección visual ni plantilla, elige una composición apropiada al contenido y mantén un sistema visual coherente. Usa 16:9 como valor predeterminado solo en ese caso.

## Portada y ritmo del deck

- Diseña una portada que identifique tema y contexto sin competir con el contenido. Usa un título breve y una imagen relevante solo si mejora la comprensión; deja la imagen fuera de la zona del título y no uses una diapositiva de contenido reducida como portada.
- Mantén la portada sobria y coherente con la identidad visual del resto. Conserva los elementos de marca de una plantilla aportada; no inventes logotipos ni marcas.
- Antes de maquetar, define una progresión narrativa y una idea principal por slide. Alterna formatos según la función de la información; no repitas mecánicamente la misma composición.
- En la conclusión, responde al propósito del deck con hallazgos o decisiones respaldados por el contenido. No agregues una diapositiva de cierre vacía o meramente decorativa.

## Composición y jerarquía

- Da a cada diapositiva un propósito principal y un título que nombre el tema concreto o exprese un hallazgo respaldado. Para diapositivas introductorias o de contexto, suele funcionar un título nominal y directo. No conviertas títulos en narración del presentador, instrucciones, anuncios vagos o eslóganes.
- Mantén una jerarquía clara entre portada, títulos, subtítulos y cuerpo. Sin una referencia, usa como guía 42 pt para la portada, 32 pt para títulos y al menos 17 pt para el cuerpo. Si el contenido no cabe, acórtalo o reorganízalo antes de reducir la letra.
- Usa una composición enfocada en vez de repetir paneles que parezcan tarjetas, botones, insignias o una interfaz. Limita etiquetas y grupos de texto a los que realmente ayuden a leer.
- Alinea elementos relacionados y sitúa las etiquetas junto a lo que describen. Mantén los conectores apartados del texto. Usa diagramas solo cuando expliquen una relación o proceso.
- Equilibra diapositivas densas y ligeras. Revisa el orden y el ritmo del conjunto, no solo cada diapositiva de forma aislada.

## Lienzo, márgenes y colisiones

- Mantén el contenido dentro del margen seguro configurado en el tema. El valor predeterminado es 0.6 pulgadas en cada borde.
- Deja espacio suficiente entre títulos, texto, tablas e imágenes. Evita solapamientos accidentales.
- Conserva proporciones, alineaciones y espacios consistentes. Comprueba saltos de línea, relleno interno, texto en negrita y ajuste de imágenes.

## Densidad, contenedores y columnas

- Cada contenedor de texto puede tener como máximo 180 caracteres, incluidos espacios y saltos de línea. Esta es una convención del compilador abierto, no una regla literal de la skill original. Se aplica a títulos, subtítulos, bloques, atribuciones y celdas.
- Si un punto excede el límite, divídelo en límites naturales de oración o palabras; no cortes palabras. Para una URL o palabra larga, usa una atribución breve que conserve la fuente.
- Expresa una idea por bloque. Prefiere unos pocos puntos concisos a un párrafo largo. No elimines evidencia que el usuario haya pedido.
- **Multi-column Split:** empieza con una columna. Si el texto no cabe a tamaño legible, reparte los bloques en dos columnas equilibradas; usa tres solo si dos no bastan y el ancho sigue siendo legible. Esta partición es una convención añadida. Respeta las columnas especificadas por el usuario, conserva el orden de lectura y equilibra altura estimada, no solo cantidad. Si tres columnas no bastan, divide el contenido entre diapositivas.
- No reduzcas el cuerpo por debajo de 17 pt solo para hacer caber contenido. Reescribe o distribuye el material.

## Imágenes, diagramas y evidencia

- Usa imágenes que representen correctamente el tema. No presentes ilustraciones generadas como fotografías de sucesos u objetos reales. Por defecto, no repitas imágenes entre slides, salvo que sean fondo o la plantilla lo requiera.
- No dibujes imágenes decorativas con Python ni construyas adornos mediante formas vectoriales programáticas. Usa recursos aportados por el usuario o imágenes obtenidas con herramientas disponibles. Decide proporción y recorte antes de colocar cada imagen; no recortes evidencia ni deformes logotipos.
- Mantén tablas y gráficos de datos como objetos editables. Conserva filas, columnas, unidades, periodos, signos y etiquetas solicitados. No conviertas evidencia en una imagen decorativa.
- No inventes cifras, citas ni relaciones causales. Basa las afirmaciones en materiales recibidos o fuentes verificables; conserva unidades, periodos, definiciones y salvedades que cambien la conclusión.
- Atribuye datos e imágenes. Usa notas del orador para referencias extensas y deja visibles en la slide las citas o divulgaciones que deba ver el público.

## Revisión visual

- Confirma el número solicitado de slides; una petición de N diapositivas significa N en total, incluida portada, salvo que se pidan N más portada.
- Revisa la secuencia y cobertura del tema, legibilidad, recortes, saltos de línea, tablas apretadas y solapamientos. Inspecciona cada diapositiva a tamaño de lectura; una hoja de contacto solo ayuda a revisar el flujo general.
- Ejecuta `scripts/check_overflow.py`. Un resultado correcto cubre límites geométricos, colisiones detectables y longitud de texto; no sustituye la inspección visual ni verifica la exactitud factual.
