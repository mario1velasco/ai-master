# QA y entrega

La automatización de esta skill usa Python estándar y `python-pptx`. Inspecciona siempre el PPTX final, no solo el JSON.

## Secuencia

1. Compila a un nombre de archivo nuevo.
2. Ejecuta `python3 scripts/check_package_integrity.py salida.pptx` y `python3 scripts/check_overflow.py salida.pptx --spec deck.json`.
3. Si hay contratos de suma, ejecuta `python3 scripts/check_table_arithmetic.py salida.pptx --spec deck.json`.
4. Si hay una plantilla de origen, ejecuta `python3 scripts/check_template_fidelity.py original.pptx salida.pptx`, permitiendo explícitamente cada slide editada.
5. Si los reportes no bastan para localizar un problema, genera `python3 scripts/inspect_presentation.py salida.pptx --output out/inspection.json`.
6. Revisa cada slide a tamaño real en PowerPoint o en un visor externo disponible. Corrige y vuelve a compilar/validar.

## Qué comprueba el QA

- CRC del ZIP, partes OPC mínimas y lectura del archivo por `python-pptx`.
- Márgenes de seguridad configurables en los cuatro lados del lienzo.
- Colisiones geométricas entre formas, con exclusiones explícitas para pares intencionales y sin tratar conectores como bloques.
- Longitud máxima de texto en formas y celdas.
- Slides requeridas para tablas/charts nativos, cantidad total de slides y fuentes declaradas.
- Charts con título placeholder vacío y valores no finitos.
- Sumas declaradas por el usuario en tablas.
- Dimensiones y huellas de objetos de una plantilla que debía preservarse.

## Límites del QA

- El ajuste tipográfico se estima por geometría y no sustituye el render real; un textbox dentro de sus márgenes puede seguir cortando texto.
- Las colisiones de cajas son una señal conservadora. Un diseño puede incluir una superposición intencional, que debe documentarse con una pareja de formas autorizada.
- El checker de plantilla no verifica equivalencia visual ni comportamiento entre PowerPoint y Google Slides.
- Los valores accesibles desde el API no garantizan que un workbook externo conserve fórmulas o lineage.
- No afirmes que se inspeccionó en PowerPoint, LibreOffice o Google Slides si no se abrió allí.

## Entrega

Guarda el PPTX final fuera del directorio temporal y no sobrescribas la plantilla original. Entrega el resultado y menciona solo problemas que afecten a su uso: por ejemplo, un chart que necesita inspección en PowerPoint o una renderización visual que no se pudo realizar.
