# CLAUDE.md — Tema 7, Sesión 3: el Asistente DropLab, de punta a punta

Valen las reglas de [`../CLAUDE.md`](../CLAUDE.md) (no ejecutar modelos sin petición, deberes del usuario, no tocar
scripts ni datos del profesor…). Guía completa para estudiar: [`EXPLICACION_tema_3.md`](EXPLICACION_tema_3.md); léela
antes de responder sobre esta sesión. Cómo ejecutar cada script: su sección 17. Recorrido del código archivo a
archivo, con números de línea: [`guia_integracion.html`](guia_integracion.html) (del profesor; igual que
`DropLab_sesion_3/alumnos/sesion_3/guia_integracion.html`).

## Qué se ve

Última sesión. Cuatro bloques, todo en local (Jetson + Ollama):

| Bloque | Idea | Scripts |
|---|---|---|
| **I · Terminar el RAG** | Repaso del bloque III de la sesión 2 (trocear, ficha, híbrida, versiones, citas). Clave del test S2 en diapos 4 y 18 | `sesion_2/10`–`15` |
| **II · Leer lo que no es texto** | VLM (`qwen3-vl`) + esquema Pydantic con `format` + comprobación en código (ticket vs caja). PDF de junio: texto / OCR (PP-OCRv6) / parser (PaddleOCR-VL-1.6) / VLM; reglas nuestras (versión en la clave, fila partida) y ficha «sin revisar» | `sesion_3/01`, `02`, `08`, `09` |
| **III · Del script al asistente** | Open WebUI → Pipe → API FastAPI → flujo LangGraph (7 nodos) → herramientas → Ollama. El modelo planifica con opciones cerradas y redacta; el código valida, enruta, contrasta y verifica | `sesion_3/03`, `04`, `05` |
| **IV · En directo** | Siete preguntas trampa; cuatro preguntas para leer una respuesta (correcta, fuentes, límites, traza) | `05_flujo.py --caso …` |
| **Extras** | Evaluar por piezas, dos configuraciones, respuesta convincente y falsa | `sesion_3/06`, `07` |

## Arquitectura del código

Todo cuelga de `DropLab_sesion_3/` (autocontenido: datos, documentos, junio, imágenes, audio, scripts de las tres
sesiones, índices y salidas guardadas) y se ejecuta desde ahí: `python practica/sesion_3/NN_….py`.

```
Navegador → Open WebUI (Docker :3000) → openwebui/droplab_pipe.py (httpx async, solo traduce)
                                              │ POST /analizar/stream (NDJSON)
                                              ▼
03_api.py → asistente/api.py (FastAPI :8000, contratos Pydantic, errores {codigo, componente, mensaje})
                                              │            ▲ 04_cliente_api.py (cualquier programa)
                                              ▼
05_flujo.py → asistente/flujo.py (LangGraph)   ·   flujo_simple.py (mismo proceso con un while)
   planificar ─(enrutar)─► leer_imagen │ consultar_datos │ buscar_documentos ─► contrastar ─► redactar ─► verificar
       │                       │                 │                 │                              ▲  1 reintento │
   Plan (Literal)          vision.py          datos.py        documentos.py                       └──────────────┘
   + reglas               (VLM+Pydantic       (SQL fijo con    (RAG S2 sobre índice
                           +caja, veredicto)   parámetros)      ampliado: 51 + 11 junio)
                                   └──────────── ollama.py: chat() /api/chat, format, tiempos, ErrorComponente
                                                 sesion2.py: importa 02, 01, 11, 12, 13 de la sesión 2 tal cual

08_leer_documentos.py (texto/ocr/vl/vlm; PaddleOCR solo en .venv-ocr) → salidas_guardadas/documentos/*.json
   → asistente/lectura.py (limpiar, unir fila partida, ficha, comprobar con capa de texto) → 09_indice_junio.py → rag/
06_evaluar.py (examen/examen_sesion_3.json por piezas) · 07_comparar.py (A 30B+VL8B vs B 4B+VL4B) · guardar_salidas.py
```

Configuración: `asistente/config.py` (variables `DROPLAB_OLLAMA`, `DROPLAB_MODELO_TEXTO`, `DROPLAB_MODELO_VISION`,
`DROPLAB_API`, `DROPLAB_INDICE`, `DROPLAB_KEEP_ALIVE`; `CTX_TEXTO=12288`, `CTX_VISION=8192`, imagen a 1024 px).

## Archivos importantes

| Archivo | Por qué importa |
|---|---|
| `practica/sesion_3/asistente/flujo.py` | `Plan` (Literal), `Estado` (traza/errores con `operator.add`), `plan_por_reglas`, nodos, `enrutar`, `contrastar`, `REGLAS_REDACCION`, `evidencias()` [S#][D#][V#], `verificar()` (citas, cifras, sustituido, CULPA/CAUSAL), `construir()` |
| `practica/sesion_3/asistente/vision.py` | Esquemas `Ticket`/`Recuento`/`Albaran`, `extraer()` con `format`, `formato_ticket` + `coherencia_ticket` + `comprobar_*`, `_veredicto()` (lectura_dudosa/discrepancia/…) escrito por código |
| `practica/sesion_3/asistente/lectura.py` | `limpiar_markdown`, `comprobar_con_capa`, `unir_fila_partida`, `SUSTITUYE` con versión, `fichas()` con `origen` por campo y `lectura` «sin revisar» |
| `practica/sesion_3/asistente/api.py` | Seis operaciones, `ConfigDict(extra="forbid")`, manejadores de `ErrorComponente` (4xx/503) y `RequestValidationError`, stream NDJSON |
| `practica/sesion_3/asistente/datos.py` | Consultas fijas con `?` y validación por regex (`PEDIDO_RE`, `SKU_RE`); `resumen_tienda` con B − A en SQL; cursor por llamada + lock |
| `practica/sesion_3/asistente/ollama.py` | `chat()` único, `Respuesta.tiempos()` (carga, entrada, salida, tokens, tok/s), `ErrorComponente` |
| `practica/sesion_3/openwebui/` | `arrancar_openwebui.sh` (`--network=host`, `WEBUI_AUTH=False`, sin RAG propio), `droplab_pipe.py`, `instalar_pipe.py`, `sonda_pipe.py` |
| `practica/sesion_3/examen/examen_sesion_3.json` | Lectura (L1–L6, campos), recuperación (B1–B6, fuentes), cálculo (C1–C4), respuesta (R1–R7, `debe`/`no_debe`) |
| `practica/sesion_3/salidas_guardadas/` | Salidas reales del Jetson para `--guardada`: `vision/`, `flujo/` (12 casos), `documentos/` (lecturas de junio), `cache_vision/` |
| `alumnos/sesion_3/` | `guia_alumno.md`, `reto.md` (7 preguntas en directo + reto con rúbrica de 40 puntos), `plantilla_reto.md` |
| `data/documentos_junio/` | Informe LOG-2026-06 v1.1 (8 págs.; T1 partida p2–3, G1 imagen p4, anexo v0.9 p6, T2 p7–8) y expediente escaneado (3 págs.) |

## Cifras clave (verificadas con los scripts o tomadas de las diapositivas)

- Ticket de abril B-MAD-MAL-ORD-0005: líneas 117,27 + 94,72 = 211,99 € (caja) frente a 231,99 € impreso →
  **discrepancia de 20 €**; 2 abonos posteriores (211,99 €) que no la explican. Ticket de marzo: coincide (11 comprobaciones).
- VLM: imagen 1060×1500 ≈ 1.580 tokens → 1024 px ≈ 1.080. G1: PaddleOCR-VL 12/12, VL 8B recortado 12/12, VL 4B 11/12
  (95 por 96), VL 8B página entera 0/12.
- Lectores (Jetson): texto 0 s; PP-OCRv6 ~2 s/pág. (conf. media 0,995); PaddleOCR-VL ~24–34 s/pág.; qwen3-vl:8b ~31–34 s.
- Índice ampliado: 51 (sesión 2) + 11 (junio, ids 51–61) = **62**; id 56 = anexo v0.9 sustituido por v1.1.
- Traza `combinada` (30B): 21 s, de ellos 19,7 s redactar (3.759 tokens de entrada, 33,5 tok/s).
- Por piezas (06): 30B+VL8B todo verde; 4B+VL4B 6/7 en respuesta (R4 sin el 108). Memoria: 19,8+6,5 GB frente a 4,5+4,2 GB.

## Avisos conocidos

- **Los directorios de `DropLab_sesion_3/` están en solo lectura** (los archivos no): no se puede crear ningún archivo.
  Fallan `11_indice.py`, `09_indice_junio.py`, `01_ver_imagen.py` en directo (caché de visión) y cualquier índice nuevo.
  Arreglo (no hecho sin permiso del usuario): `chmod -R u+w clase_03/DropLab_sesion_3`. Al ejecutar desde aquí, usar
  `PYTHONDONTWRITEBYTECODE=1`.
- Modelos por defecto: 30B + `qwen3-vl:8b-instruct`. En el portátil: `DROPLAB_MODELO_TEXTO=qwen3:4b-instruct`,
  `DROPLAB_MODELO_VISION=qwen3-vl:4b-instruct` (sesión 3) y `--llm qwen3:4b-instruct` (sesión 2, scripts 13–15).
  Hace falta `bge-m3`. No descargar modelos sin petición.
- PaddleOCR va en un entorno aparte (`.venv-ocr`, `requirements_ocr.txt`); no está ni hace falta en el `.venv` del tema.
- El enunciado cita un «anexo B» y `Deberes_sesion_3.docx` que no vienen: la respuesta del analista es la diapo 66 de la S2.
- `07_transcribir.py` sigue pidiendo `llamada_0704_{central,tienda}.wav`, que no vienen (ver `../clase_02/CLAUDE.md`).
- Ejercicio 4 de la entrega: «alguna de las cuatro respuestas tiene un error». No revelar cuál ni dar las cifras de junio.

## Qué nos sirve para `travel-agency/`

Relación con las fases de [`../../travel-agency/PROYECTO.md`](../../travel-agency/PROYECTO.md) (sección 10). Esta
sesión es la que más se parece al proyecto: un agente local con datos (SQL) + documentos (RAG), detrás de una API y
medido. Son **patrones para copiar**, no código para importar (allí: uv workspace, Python 3.12, ruff/ty).

| Fase | Qué copiar de esta sesión | Dónde | Ojo |
|---|---|---|---|
| **1b. Telemetría** | Traza por nodo `{nodo, segundos, herramienta, detalle}` acumulada en el estado; tiempos de Ollama por llamada (carga, entrada, salida, tokens, tok/s) | `flujo.py` (`_paso`, `Estado.traza`), `ollama.py` (`Respuesta.tiempos()`) | Viene de la API nativa `/api/chat`: confirma el aviso de `PROYECTO.md` §5 sobre `/v1`. La traza se ve pero no se guarda: el JSONL es nuestro (ej. 5) |
| **1c. Contratos / errores** | Error con nombre `{codigo, componente, mensaje}` (`ErrorComponente`) que viaja hasta el cliente; mapa código → HTTP (4xx petición, 503 pieza caída) | `ollama.py`, `api.py` (`ESTADO_HTTP`, manejadores) | Encaja con un modelo de error en `contracts/`; 10 pruebas de integración lo comprueban (06 `--parte integracion`) |
| **4. Conversión** | **PaddleOCR ya tiene referencia en el repo**: PP-OCRv6 (líneas + confianza) frente a PaddleOCR-VL-1.6 (tablas en HTML, gráficos como tabla); página → imagen a 150 ppp; conservar pie; motor «transformers» (PyTorch + CUDA); entorno aparte; limpiar HTML → filas, unir fila partida, comprobar cifras contra la capa de texto, campo `lectura` «sin revisar» | `08_leer_documentos.py`, `asistente/lectura.py`, `requirements_ocr.txt` | `PROYECTO.md` dice PP-StructureV3; aquí se midió PaddleOCR-VL-1.6. GTX 1650 de 4 GB: medir antes (en CPU ~40 s/pág.). Las reglas de ficha son de ESTE formato. Actualizar la fila 4 de `travel-agency/AGENTS.md` («PaddleOCR no aparece en el repo») |
| **5. Text-to-SQL** | Consultas **fijas con parámetros** (`?`) + validación del valor por regex para las preguntas frecuentes; el SQL del modelo (capa semántica) solo para el resto; diferencias calculadas en SQL | `datos.py` | Es el caso «Ataque» de los casos dorados: «1; DROP TABLE» → 422 sin tocar la base |
| **6. Agente** | Alternativa al *tool calling* libre: el modelo rellena un `Plan` con opciones cerradas (`Literal`) por `format`; el código lo valida, lo **corrige** con reglas y tiene plan B por palabras clave; `enrutar` determinista; nodo `contrastar` (versiones, fuentes automáticas, límites) antes de redactar; evidencias numeradas por código; `verificar` sin IA (citas, cifras, sustituido, culpa/causa) con 1 reintento | `flujo.py`, `flujo_simple.py` | Primero el bucle sin framework (`flujo_simple.py`, como pide la fila 6); LangGraph cuando haya ramas, reintentos o aprobación humana. Comparar plan cerrado frente a tool calling con la evaluación, no por gusto |
| **6. Modelos** | Con el código haciendo lo difícil, **4B + VL 4B casi empata con 30B + VL 8B** (6/7 frente a 7/7) | `07_comparar.py`, diapo 64 | Respalda usar el 4B. Pero el 4B omitió la cifra clave (108 → 7) y nadie lo vio: los casos dorados deben comprobar hechos concretos |
| **5/6. Configuración** | Modelos y URLs por variables de entorno; **un único `num_ctx` por modelo**: si dos llamadas usan otro, Ollama recarga el modelo (~25 s por pregunta, medido); `keep_alive` | `config.py` | Clave en travel-agency: `agent/` y `text2sql/` usan el **mismo** Qwen3-4B; si piden `num_ctx` distintos, se recargará en cada pregunta mixta |
| **7. API** | Contratos Pydantic con `extra="forbid"`; operaciones de 2–3 líneas que llaman a funciones que ya existen; `/salud` sin modelos; `/analizar/stream` (NDJSON) para enseñar el progreso; subida multipart; cliente de ejemplo | `api.py`, `03_api.py`, `04_cliente_api.py` | Comparar con la estructura de triage (fila 7): la lógica fuera de la API, la API solo valida, llama y devuelve |
| **8. RAG** | Índice ampliado que **conserva los id** del anterior; la **versión entra en la clave** («LOG-2026-06 v0.9» ≠ «v1.1»); RAG detrás de una función con lock; un único RAG (no el de la interfaz) | `09_indice_junio.py`, `lectura.py`, `documentos.py` | Es el caso «política vs ley / versión derogada»: la regla «sustituye a» de la S2 no basta si el código no cambia entre versiones |
| **10. Evaluación** | Examen **por piezas** (lectura, recuperación, cálculo, respuesta con `debe`/`no_debe`, integración) para saber *dónde* falla; dos configuraciones con carga, memoria y tiempo; **salidas guardadas reales** reproducibles sin modelos | `06_evaluar.py`, `examen/examen_sesion_3.json`, `07_comparar.py`, `guardar_salidas.py`, `salidas_guardadas/` | Las salidas guardadas son una buena base para los tests sin Ollama (mock determinista de triage). «Si falla con todos los modelos, el problema es el dato, el índice o el código» |
| **10. Verificación** | Limitación documentada: el verificador acepta una cifra si está en *alguna* evidencia, no en la citada (`extra_falla`: 60 en vez de 40, verificación limpia) | `flujo.py` (`verificar`), diapo 61 | Hacerlo mejor desde el principio: cifra en la fuente citada; y la recuperación de tablas partidas se evalúa aparte |
| **13. Docker / interfaz** | Open WebUI en Docker con `--network=host`, volumen para datos, imagen con versión fija; Pipe como adaptador fino que llama a la API (sin lógica, `httpx` asíncrono) | `openwebui/` | Opcional como frontal del proyecto. Licencia de Open WebUI: BSD-3 + cláusula de marca. `WEBUI_AUTH=False` solo para el aula |
| **Seguridad** | Barreras en código: parámetros en vez de texto, regex del valor, `extra="forbid"`, sin RAG en la interfaz; lo pendiente para producción (usuarios, permisos, registro) | `datos.py`, `api.py`, diapo 58 | Cuadra con la tabla de seguridad de `PROYECTO.md` §9 |

No aplica hoy: el VLM de tickets (el proyecto no recibe imágenes) y `qwen3-vl` (no cabe junto al 4B en 4 GB de VRAM).
Si el corpus tuviera gráficos o escaneados, ver el bloque II antes de decidir el lector.
