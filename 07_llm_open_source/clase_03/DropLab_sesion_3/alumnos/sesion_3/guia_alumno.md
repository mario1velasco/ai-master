# Sesión 3 · Guía del alumno · El Asistente DropLab

Última sesión. Hoy **terminamos el RAG** que dejamos a medias en la sesión 2, leemos documentos que **no son texto**
(un ticket, un PDF escaneado, tablas que saltan de página y un gráfico) y lo vemos todo funcionar **de punta a punta**
en un asistente local que se usa desde el navegador. El código ya está hecho: vais a **ejecutar, observar, cambiar
cosas pequeñas e interpretar** los resultados.

> Regla de las tres sesiones: **el código calcula y comprueba; el modelo lee, entiende y redacta; tú verificas.**

| Min | Bloque | Prácticas |
|---|---|---|
| 0–8 | Apertura | — |
| 8–45 | I · Terminar el RAG | 5 y 6 (las de la sesión 2) |
| 45–85 | II · Leer lo que no es texto | 1 (ticket) y 2 (PDF de junio) |
| 85–95 | Descanso | — |
| 95–115 | III · Del script al asistente | 3 (API y flujo) |
| 115–150 | IV · El asistente, en directo | reto en directo (`reto.md`) |

## 0. Antes de empezar

En el equipo del aula (o en el tuyo, ver el final), desde la carpeta del proyecto:

```bash
cd ~/projects/jetson-edge/llms/DropLab
source .venv/bin/activate
python practica/sesion_3/00_comprobar_entorno.py      # todo en verde (o casi)
```

Casi todo admite `--guardada`: enseña una salida **real** guardada en el Jetson, sin llamar a ningún modelo. Úsala si
tu equipo va lento: lo que importa es interpretar.

---

## Bloque I · Terminar el RAG

### Práctica 5 · Preparar y buscar

```bash
python practica/sesion_2/10_corpus.py                        # 10 fuentes → 51 fragmentos, con su ficha
python practica/sesion_2/10_corpus.py --trocear calendario   # antes y después de cortar un documento
python practica/sesion_2/11_indice.py                        # 51 vectores (bge-m3) en DuckDB
python practica/sesion_2/12_buscar.py "¿Hasta qué día estuvo vigente el Pack 4?" --explicar
```

- [ ] ¿Qué datos de la ficha pone el documento y cuáles deduce el código?
- [ ] En la búsqueda, ¿qué fragmento sale primero? ¿Es el que manda? ¿Qué hace el código?

### Práctica 6 · Responder con fuentes

```bash
python practica/sesion_2/13_preguntar_documentos.py "¿Hasta qué día estuvo vigente el Pack 4?"
python practica/sesion_2/13_preguntar_documentos.py "¿Cuándo empezaron las obras?"
```

- [ ] Abre la fuente citada en la segunda: ¿dice «empezaron» o «programado»? ¿Lo ha detectado el verificador?

(Si tu equipo no tiene el modelo de 30B: `--llm qwen3:4b-instruct`. Los scripts de la sesión 2 eligen el modelo con
`--llm`; los de la sesión 3, con las variables `DROPLAB_MODELO_*`.)

---

## Bloque II · Leer lo que no es texto

### Práctica 1 · Leer y comprobar un ticket

```bash
python practica/sesion_3/01_ver_imagen.py ticket_abril.png --sin-libre
python practica/sesion_3/02_validar.py                                           # sin modelo, instantáneo
python practica/sesion_3/01_ver_imagen.py ticket_abril_muy_borroso.png --guardada   # imagen SINTÉTICA
```

- [ ] ¿Ha leído bien el total? ¿Coincide con caja? ¿Con la suma de sus propias líneas?
- [ ] El ejemplo C de `02_validar.py` pasa la validación. ¿Qué lo delata?
- [ ] En la muy borrosa, ¿qué dice el modelo de su propia legibilidad? ¿Qué dice el código?

### Práctica 2 · Leer los PDF de junio

Segundo encargo de dirección: el cierre de la reposición de junio. Solo hay dos PDF (`data/documentos_junio/`): un
informe de 8 páginas (tablas, un gráfico que es una imagen y un anexo con un borrador) y un expediente **escaneado**.

```bash
python practica/sesion_3/08_leer_documentos.py              # qué hay en cada página
python practica/sesion_3/08_leer_documentos.py --antes      # el lector de la sesión 2, con estos PDF
python practica/sesion_3/08_leer_documentos.py --leer escaneado 2 --con ocr --guardada   # OCR (PP-OCRv6)
python practica/sesion_3/08_leer_documentos.py --leer informe 4 --con vl --guardada      # PaddleOCR-VL
python practica/sesion_3/08_leer_documentos.py --leer informe 4 --con vlm --guardada     # qwen3-vl (VLM general)
python practica/sesion_3/08_leer_documentos.py --capas escaneado 2 --guardada          # qué hace PaddleOCR solo y qué nuestro código
python practica/sesion_3/08_leer_documentos.py --capas informe 8 --guardada --solo-modelo  # raw de la fila partida
python practica/sesion_3/08_leer_documentos.py --capas informe 8 --guardada --solo-reglas  # cómo la une nuestro código
python practica/sesion_3/08_leer_documentos.py --comparar   # tiempos y cifras comprobadas
python practica/sesion_3/09_indice_junio.py                 # ficha de cada página e índice ampliado
python practica/sesion_3/09_indice_junio.py --ver 56        # el anexo con el borrador
```

(En el Jetson, el profesor lo lanza **en directo** con `.venv-ocr/bin/python … --leer …` sin `--guardada`: PaddleOCR
en la GPU.)

- [ ] ¿Qué código y qué estado pone el lector de la sesión 2 a cada página? ¿Por qué?
- [ ] El OCR lee cada número del parte de incidencia. ¿Qué le falta para que sirva a un RAG?
- [ ] En la pág. 4, ¿cuántas cifras de la lectura **no** están en el texto del PDF? ¿De dónde salen? ¿Y el VLM general?
- [ ] ¿Por qué la ficha del anexo dice «LOG-2026-06 v0.9 · sustituido» si su pie dice «v1.1»?
- [ ] ¿Qué significa «sin revisar» en la ficha? ¿Qué valores no se pueden comprobar nunca con el PDF?
- [ ] En `--capas`, separa: lo que configuramos antes (imagen, gráficos activados, conservar el pie), el texto/HTML que devolvió el modelo, la limpieza mecánica de HTML a filas Markdown y las reglas que escribimos para este documento (código, estado, versión, unir la fila partida).
- [ ] ¿Qué regla te parece una decisión técnica nuestra y cuál necesita que la confirme la persona responsable del proceso? ¿Quién debería validar que «APROBADO» en la página 1 se propague al resto?

---

## Bloque III · Del script al asistente

### Práctica 3 · La API y el flujo

```bash
python practica/sesion_3/03_api.py                       # si no está ya; contrato en http://<equipo>:8000/docs
python practica/sesion_3/04_cliente_api.py consulta --pedido "1; DROP TABLE ventas"
python practica/sesion_3/05_flujo.py --dibujar
python practica/sesion_3/05_flujo.py --caso junio_grafico          # o con --guardada
```

En `/docs`: `POST /documentos/buscar` → «Try it out» → una pregunta de junio. Mira el campo `lectura`.

- [ ] ¿Qué código HTTP devuelve el pedido malicioso? ¿Qué `componente` falla? ¿Llega al SQL?
- [ ] En el flujo de junio, ¿qué tareas planifica? ¿Por qué no consulta los datos (SQL)?
- [ ] ¿Qué comprobaciones añade el código antes de redactar?

---

## Bloque IV · El asistente, en directo

El profesor lanza siete preguntas difíciles en Open WebUI (`http://<jetson>:3000`, modelo **DropLab Analista**) y las
leemos juntos. Las preguntas y las cuatro preguntas para leer una respuesta, en `alumnos/sesion_3/reto.md` (parte 1).

- [ ] Antes de cada pregunta: ¿qué debería contestar y dónde está?
- [ ] Después: ¿es correcta? ¿La respaldan las fuentes (abre una)? ¿Dice lo que no sabe? ¿Se ve qué hizo?

**Para entender cómo se conecta todo** (modelo, herramientas, flujo, API y Open WebUI): abre
`alumnos/sesion_3/guia_integracion.html` en el navegador. Va archivo a archivo, en orden y con los números de línea, y
acaba con lo que haría falta para llevarlo a producción.

---

## Entrega final (una sola, sesiones 2 y 3, individual)

En `Deberes_sesion_3.docx`: (1) el RAG con una decisión cambiada y medida (`14_evaluar_rag.py`) y (2) cinco frases
para dirección (la respuesta de `15_analista.py`): antes, ejercicios 3 y 4 de la sesión 2; (3) el **reto Malasaña**
(`reto.md`, parte 2, con `plantilla_reto.md`); (4) el **cierre de junio**; y (5), opcional, **hacia producción**.

Para casa, si queréis más (no cuenta para nota): `06_evaluar.py` (examen por piezas), `07_comparar.py` (dos
configuraciones), `05_flujo.py --sin-framework`, y los extras de clase: `05_flujo.py --caso extra_falla --guardada`
(una respuesta convincente y falsa) y `08_leer_documentos.py --grafico` (el gráfico a un VLM).

---

## Si trabajas en tu portátil

| Tu equipo | Qué hacer |
|---|---|
| 16 GB de RAM | Tres descargas: `ollama pull qwen3:4b-instruct`, `ollama pull qwen3-vl:4b-instruct` y `ollama pull bge-m3`. Para la sesión 3: `export DROPLAB_MODELO_TEXTO=qwen3:4b-instruct DROPLAB_MODELO_VISION=qwen3-vl:4b-instruct`; para los scripts 13–15 de la sesión 2: `--llm qwen3:4b-instruct`. Más lento sin GPU dedicada. Ojo: el 4B leyó 95 donde ponía 96 en el gráfico de junio |
| 8 GB o sin Ollama | Usa la API del aula: `export DROPLAB_API=http://<jetson>:8000` y `04_cliente_api.py`; y las salidas `--guardada` |
| PaddleOCR en tu equipo | Opcional: entorno aparte con `requirements_ocr.txt`. Con GPU NVIDIA, PyTorch con CUDA; sin GPU funciona, lento (~40 s por página). El índice ampliado no lo necesita: usa las lecturas guardadas |
| Mac, Windows o Linux con Docker | Open WebUI también corre ahí; la Pipe necesita la dirección de la API |

Dependencias: `pip install -r requirements.txt -r requirements_sesion_3.txt`.
