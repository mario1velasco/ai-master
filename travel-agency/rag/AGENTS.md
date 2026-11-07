# AGENTS.md — `rag/`

> Estado: **fase 3 terminada**. Corpus externo con `rag/corpus/SOURCES.md` (TRAVEL-003) y 26 documentos propios en
> `corpus/empresa/` (TRAVEL-004). El paquete sigue vacío: la fase 3 es solo de datos. Siguiente: fase 4 (conversión).

## Propósito

Corpus documental (`corpus/`), conversión a Markdown con PaddleOCR (`conversion/` → `markdown/`) y búsqueda híbrida BM25 + FAISS + RRF + reranker (sección 4).

Depende de: `contracts`, `telemetry`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/rag/__init__.py`: punto de entrada del paquete (`import rag`).
- `tests/`: tests con pytest.
- `corpus/leyes/`
- `corpus/seguridad/`
- `corpus/salud/`
- `corpus/empresa/`
- `corpus/general/`
- `conversion/`
- `markdown/`

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest rag/tests
```

Variables en `.env` (copiar de `.env.example`): `RAG_EMBEDDING_MODEL`, `RAG_RERANKER_MODEL`.

## Corpus y licencias

- `corpus/SOURCES.md`: una fila por archivo (`Archivo` · `Título` · `URL` · `Descarga` · `Licencia` · `Carpeta` ·
  `En git` · `SHA-256`). Licencia poco clara → el documento no entra.
- `corpus/seguridad/aesa/` y `corpus/seguridad/exteriores/` son **de uso privado**: están en `.gitignore` y se
  vuelven a descargar desde la URL de su fila. Los archivos de más de 10 MB también van fuera de git (regla por
  archivo en `.gitignore`).
- Los originales no se tocan: la conversión (fase 4) escribe en `markdown/`.

Documentos de `empresa/` (TRAVEL-004): Markdown al estilo de DropLab (`politica_reembolsos.md` del tema 7), con esta
cabecera, que se lee con las mismas expresiones que `leer_md` de `S2/10_corpus.py`:

```text
# Viajes Nimbo · <título>
Documento <CÓDIGO> · Versión <n> · Vigente desde <dd/mm/aaaa>
Responsable: <área>
Ámbito: <subcarpeta> · Público: cliente|interno
```

- `Público: interno` solo en `interno/` (no se cita a clientes); `pruebas/documento_trampa.md` lleva una instrucción
  inyectada a propósito y no es documentación real.
- Versiones: `politicas/historico/` guarda la política de cancelación antigua (POL-CAN-2023-01, hasta el 28/02/2025);
  la vigente dice «sustituye a POL-CAN-2023-01». Las reservas de `database/data/` caen a los dos lados del cambio.
- Los datos (sedes, horarios, niveles, plazos) son los mismos en todos los documentos y cuadran con `database/`
  (niveles `basico`/`plata`/`oro`, `paquete`/`solo_vuelo`, `turista`/`business`, 6 aerolíneas, compensaciones
  250/400/600 €). Si cambias una cifra, búscala en todos (`grep -rn` en `corpus/empresa/`), FAQ incluida.
- Correos y webs solo en `viajesnimbo.example`; empresa, CIF y licencia, ficticios.

Comprobar el corpus cuando cambie (desde `travel-agency/`; no hay tests, es un entregable de datos):

```bash
cd rag/corpus
# Huellas: todos OK (las filas de empresa/ llevan «—» y se saltan)
grep '^| [a-z]' SOURCES.md | awk -F' \\| ' '{gsub(/^\| /,"",$1); gsub(/ \|$/,"",$8); if ($8 != "—") print $8"  "$1}' | sha256sum -c --quiet
# Cada archivo con su fila: sin salida
diff <(find . -type f ! -name .gitkeep ! -name SOURCES.md | sed 's|^\./||' | sort) \
     <(grep '^| [a-z]' SOURCES.md | awk -F' \\| ' '{gsub(/^\| /,"",$1); print $1}' | sort)
cd ../..
git check-ignore rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores   # las dos carpetas
git ls-files rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores       # sin salida
find rag/corpus -type f -size +10M | xargs -r git check-ignore -v            # cada uno, ignorado
```

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
- Qué hay en cada carpeta: `leyes/` (EUR-Lex y BOE, PDF), `salud/` (guía del Ministerio de Sanidad y Tu Europa),
  `seguridad/` (EASA, AESA y Exteriores, HTML tal cual se sirve), `general/tabiji/` (5 tablas Parquet en inglés,
  registros y no documentos: la fase 4 tiene que pasarlos a texto). Detalle y licencias en `SOURCES.md`.
- El Yellow Book de CDC no se puede descargar gratis (y CDC bloquea `curl`): se descartó, ver `PROYECTO.md` §4.
- Las páginas HTML cambian en origen: una nueva descarga da otra huella y hay que actualizar su fila.
