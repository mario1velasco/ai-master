# CLAUDE.md — Tema 7, Sesión 2: DropLab Analyst con datos, voz y documentos

Valen las reglas de [`../CLAUDE.md`](../CLAUDE.md) (no ejecutar modelos sin petición, deberes del usuario, no tocar
scripts ni datos del profesor…). Guía completa para estudiar: [`EXPLICACION_tema_2.md`](EXPLICACION_tema_2.md);
léela antes de responder sobre esta sesión. Cómo ejecutar cada script: su sección 16.

## Qué se ve

Tres bloques sobre el caso DropLab, todo en local (Ollama en una Jetson de 64 GB):

| Bloque | Idea | Scripts |
|---|---|---|
| **I · Datos con garantías** | Capa semántica (vistas DuckDB con el negocio dentro y comentarios) + modelo capaz (`qwen3:30b-a3b`, MoE) + verificador de cifras. Examen con respuestas a mano: 58 % → 91 % | 01, 02, 04 |
| **II · La voz** | Un audio son números; Whisper (log-mel 128 × 3000, codificador + decodificador) escribe como un LLM y alucina; un canal por persona, solo voz, pista, contrastar | 06, 07, 08, 09 |
| **III · Documentos (RAG local)** | Trocear por estructura + ficha por fragmento + bge-m3 en DuckDB + BM25 + RRF + regla «sustituido» + citas `[F#]` puestas por código + verificador | 10, 11, 12, 13, 14 |
| **Todo junto** | Analista con dos herramientas: `consultar_datos` `[S#]` y `buscar_documentos` `[D#]` | 15 |

## Arquitectura del código

Todo cuelga de `DropLab_sesion_2/` y se ejecuta desde ahí: `python practica/sesion_2/NN_….py`.

```
data/datos/*.csv ──► sesion_1/03 (DATA, cifras de verdad)
        │
        ▼
02_capa_semantica  CSV en esquema `crudo` → vistas en `main` + COMMENT ON → esquema automático + GUIA
        │           (barreras SQL de sesion_1/08: solo SELECT, 1 sentencia, sin archivos, 50 filas)
        ▼
01_preguntar_datos  bucle tool calling (ejecutar_sql) + verificador cifras_sin_respaldo()  ◄── 04_examen (examen/*.json)
        │
        │   data/audio/*.wav ──► 06_ver_audio (log-mel, turnos por energía) ──► 07_transcribir (Whisper)
        │                                                 08_ver_transcripcion / 09_panel ◄──┘ transcripciones/*.json
        ▼                                                                                     │
15_analista ◄── 13_preguntar_documentos ◄── 12_buscar ◄── 11_indice ◄── 10_corpus ◄── data/documentos/ + llamada
                 (REGLAS + verificar)      (Buscador:     (Ollama /api/   (rag/corpus.jsonl)
                                            sem/BM25/RRF)  embed → rag/indice_<modelo>.duckdb)
                                    14_evaluar_rag (examen/examen_rag.json: Hit@k, MRR, respuestas)
```

Importaciones: 02 → `sesion_1/03`, `sesion_1/08` · 01 → 02, 08 · 04 → 01 · 07/08/09 → 06 · 09 → 08 ·
12 → 11 · 13 → 11, 12 · 14 → 11, 12, 13 · 15 → 02, 01, 12, 13. Los scripts se importan con `import_module`
porque empiezan por número.

## Archivos importantes

| Archivo | Por qué importa |
|---|---|
| `practica/sesion_2/02_capa_semantica.py` | `VISTAS`, `COMENTARIOS`, `GUIA` (incluye «datos que NO existen»), `esquema()` generado desde `duckdb_views()`/`duckdb_columns()`, `COMPROBACIONES` contra el 03 |
| `practica/sesion_2/01_preguntar_datos.py` | Bucle `conversar()` (rondas, última sin tools, `think: False`, temperatura 0), `numeros()` (formato ES/EN), `cifras_sin_respaldo()` y reintento único |
| `practica/sesion_2/04_examen.py` + `examen/{bateria,validacion,prueba_final}.json` | Examen 13/10/10 con `esperado`, `texto_esperado`, `debe_negar`; corrección por cifras ±0,011 y lista `NEGACIONES` |
| `practica/sesion_2/10_corpus.py` | Lectores MD (`## `), PDF (página, limpieza de ruido, `unir_lineas`) y llamada (2 turnos con solape); ficha; `texto_indexado` con cabecera; regex «sustituye a X» |
| `practica/sesion_2/11_indice.py` | Embeddings por lotes con Ollama, `PREFIJOS` por modelo, tabla `fragmentos` con ficha + `FLOAT[]` |
| `practica/sesion_2/12_buscar.py` | Clase `Buscador`: coseno en DuckDB, BM25 propio (stopwords, sin tildes), RRF k=60 sobre top-20, añade el vigente |
| `practica/sesion_2/13_preguntar_documentos.py` | `REGLAS` (cita o no se afirma, «no consta», manda lo aprobado, fechas, llamada = testimonio) y `verificar()` |
| `practica/sesion_2/14_evaluar_rag.py` + `examen/examen_rag.json` | 16 preguntas con `fuentes` (`archivo#página`) y `hechos` (alternativas) |
| `practica/sesion_2/15_analista.py` | Dos herramientas, numeración `[S#]`/`[D#]` por código, rechazo de respuestas sin consultar |
| `practica/sesion_2/07_transcribir.py` | `word_timestamps`, `clip_timestamps` (solo voz), `initial_prompt` (pista), umbral dudosa 0,70 |
| `data/documentos/` | 6 MD + 3 PDF (expediente de 8 págs. con copias; manual de 8 págs.). Trampas: versiones, fechas, copias, transcripción |

Generados (no versionar): `practica/sesion_2/rag/` (corpus e índices), `transcripciones/*.html`, `panel/`,
`figuras_audio/`.

## Cifras clave (verificadas con los scripts)

- Capa: Malasaña 40.000 → 26.000 € · empresa 96.000 → 81.000 € · cesta 120/120 pedidos, 467 → 304 uds ·
  pedidos 4+ **108 → 7** (2 uds: 1 → 63; 3 uds: 11 → 50) · HIST-JOIN-001: 2 abonos, 30 € · stock: 8 intervalos, 4 SKU, 48 h-SKU.
- Examen 33 preguntas: 30B crudo 58 % · 4B crudo 61 % · 4B capa 67 % · **30B capa 91 %** · gpt-oss 20B 97 % (~30 s).
- Coste: 4B 3,2 GB y 7,3 tok/s · 30B-a3b 18 GB y 8,5 tok/s.
- Audio: 113,3 s, 2 canales, 16 kHz, 16 bits, 3,6 M números, 7,3 MB, 13 turnos (umbral −40 dB).
- RAG: 10 fuentes → 51 fragmentos (21 MD + 17 PDF + 13 llamada); bge-m3 1.024 dims; recuperación top-3 bge-m3
  híbrida 16/16; respuestas 30B 16/16/16 (24 s), 4B 16/16/15/10 (35 s).

## Avisos conocidos

- Los scripts usan por defecto `qwen3:30b-a3b-instruct-2507-q4_K_M` (18 GB): en este portátil no cabe. Pasar
  `--modelo qwen3:4b-instruct` (01, 04) o `--llm qwen3:4b-instruct` (13, 14, 15). RAG: `ollama pull bge-m3`.
- `07_transcribir.py --modo canales` lee `data/audio/llamada_0704_{central,tienda}.wav`, que **no vienen en el
  zip**. Se crean con `ffmpeg -af "pan=mono|c0=c0"` / `c0=c1` (con `channelsplit` sale WAV extensible que `wave` no lee).
- `12_buscar.py` llama a Ollama también en `--modo palabras` (calcula siempre la lista semántica).
- Citados pero ausentes: `03_monitor_recursos.py`, `sesion_1/04_conectar_ollama.py` (está en
  `../clase_01/Ejercicios/practica/`), `docs/sesion_2/…`, `experimentos/`. El enunciado cita un anexo que no
  viene: la respuesta del analista está en la diapositiva 66.
- La barrera SQL no bloquea `crudo.*`: la capa esconde las tablas, no las prohíbe.
- Whisper (ejercicio 2) se instala aparte: PyTorch + `requirements_audio.txt` (GB); no instalar sin petición.

## Qué nos sirve para `travel-agency/`

Relación con las fases de [`../../travel-agency/PROYECTO.md`](../../travel-agency/PROYECTO.md) (sección 10). Son
**patrones para copiar**, no código para importar (allí: uv workspace, Python 3.12, ruff/ty, Pydantic).

| Fase | Qué copiar de esta sesión | Dónde | Ojo |
|---|---|---|---|
| **2. Base de datos** (vistas, diccionario, tests de integridad) | Tablas en esquema oculto + vistas que ya calculan lo difícil (neto, periodo por la fecha correcta, agregar antes de unir) + `COMMENT ON` en cada vista/columna + `COMPROBACIONES` con cifras calculadas a mano | `02_capa_semantica.py` (`VISTAS`, `COMENTARIOS`, `comprobar()`) | Mismo diseño que las `v_*` de `PROYECTO.md` §3; las comprobaciones son la semilla de los tests de integridad |
| **5. Text-to-SQL** (línea base) | Esquema **generado** desde los comentarios (no escrito a mano) + `GUIA` (qué vista para qué pregunta, cálculos dentro del SQL, «datos que NO existen») + error de DuckDB devuelto al modelo + `num_ctx` fijo | `02` (`esquema()`, `construir_system_prompt()`), `01` (`conversar()`) | Con la capa, el **4B solo llegó al 67 %** («une vistas sin necesidad y suma unidades cuando se piden pedidos»): vistas aún más directas, ejemplos y función fija para las preguntas frecuentes. La barrera de clase **no tiene lista blanca de vistas**: en travel-agency hay que añadirla (parsear las tablas referenciadas) |
| **5/6. Verificador** | `numeros()` + `cifras_sin_respaldo()`: cada cifra de la respuesta debe salir de un resultado; un reintento y luego aviso | `01_preguntar_datos.py` | Solo comprueba que la cifra *existe*, no su significado: la evaluación debe mirar también el SQL |
| **6. Agente** | Dos herramientas con citas numeradas por el código (`[S#]` SQL, `[D#]` documentos) y rechazo de respuestas sin haber consultado; última ronda sin tools | `15_analista.py` | El analista no consultó la cifra clave (108 → 7): los casos dorados deben comprobar **qué** consultó, no solo que cite |
| **8. RAG** | Trocear por estructura (sección `##`, página, turno) con tope de palabras; ficha por fragmento (`cita`, `codigo`, `fecha`, `estado`, `responsable`); cabecera de contexto en el texto indexado; regla «sustituye a X» → `sustituido` y añadir el vigente; RRF k=60 sobre top-20; `PREFIJOS` por modelo | `10_corpus.py`, `11_indice.py`, `12_buscar.py` | Encaja con el caso «política vs ley / versión derogada» (`vigente_desde`). Clase usa bge-m3 vía Ollama `/api/embed` + DuckDB; el proyecto decidió `sentence-transformers` + FAISS Flat: DuckDB vale para prototipar. El tokenizador BM25 de clase parte «261/2004» en dos tokens: adaptarlo a los códigos legales |
| **8. Respuesta con citas** | `REGLAS` (sin cita no se afirma, «no consta», manda lo vigente, significado de cada fecha, transcripción = testimonio) + `verificar()` (citas existen, cada frase cita, cifras en su fuente, sustituido mencionado) + lista de fuentes construida por código | `13_preguntar_documentos.py` | Una cita real no prueba fidelidad (diap. 63): hace falta juez o revisión humana (fase 10) |
| **5/8/10. Evaluación** | Examen JSON con `esperado`/`hechos` alternativos y `debe_negar`; **tres conjuntos** (diseñar / validar / decidir); recuperación sin LLM (Hit@k + MRR) separada de la respuesta (hechos, cita esperada, verificación limpia); temperatura 0 | `04_examen.py`, `examen/*.json`, `14_evaluar_rag.py` | Mismo espíritu que train/dev/test **por plantilla** de `PROYECTO.md` §6. Corrección por cifras ±0,011 es generosa: execution accuracy es más estricta |
| **1b/5. Telemetría** | Segundos totales, `load_duration` (carga), `prompt_eval_count` (tokens de entrada), rondas y nº de consultas, de la API nativa `/api/chat` | `01_preguntar_datos.py` (`conversar()`) | Confirma el aviso de `PROYECTO.md` §5: con `/v1` se pierden esos tiempos |
| **9. Fine-tuning** | El plan de adaptar Whisper: datos revisados por humanos, separar por llamada (no por trozo), LoRA, medir antes y después en datos no vistos | Diapositiva 42; enlace 16 | Misma lógica que separar por plantilla y comparar con el escalón 3 |
| **Modelos / hardware** | Modelo MoE (`30b-a3b`): memoria = total, velocidad = activos; 18 GB → **no cabe** en el equipo del proyecto (16 GB RAM, 4 GB VRAM) | Diapositivas 19–20 | Mantener el 4B; la palanca grande es cómo se presentan los datos, no el tamaño |

No aplica hoy: Whisper y el audio (el proyecto no tiene entrada por voz); si algún día la tuviera, ver bloque II.
