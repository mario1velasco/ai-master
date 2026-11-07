# TRAVEL-003 · Reunir el corpus externo con sus fuentes y licencias

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`rag/corpus/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-07 |
| Etiquetas | rag, corpus, licencias, fase-3, datos |

## Historia de usuario

**Como** responsable del RAG de Viajes Nimbo, **quiero** tener reunidos los documentos externos (leyes, salud, seguridad y general) con su fuente, su licencia y su huella, **para que** la fase 4 los convierta sabiendo de dónde viene cada uno y nada de uso privado acabe en git.

## Contexto

`rag/corpus/` solo tiene las cinco carpetas vacías (`.gitkeep`). `PROYECTO.md` §4 fija las fuentes por carpeta y la regla de licencias: cada documento se apunta en `rag/corpus/SOURCES.md` y, si la licencia no está clara, no entra. AESA y Exteriores solo permiten uso privado, así que se descargan pero no se suben (`corpus/seguridad/aesa/` y `corpus/seguridad/exteriores/` en `.gitignore`, que todavía no tiene esas reglas). Es la primera mitad de la fase 3; los documentos propios de `empresa/` van en TRAVEL-004.

Es un ticket **de datos, sin código**: el entregable son archivos, una tabla y reglas de `.gitignore`, y cada criterio se comprueba con una revisión o con comandos que ya existen (`sha256sum`, `git check-ignore`, `git ls-files`, `find`). La fase 4 lee `SOURCES.md` para poner `fuente`, `url` y `licencia` en cada `.md`, así que una fila que falte se nota allí.

**Referencias leídas:** `travel-agency/PROYECTO.md` §4 («Sobre las licencias», «Fuentes por carpeta», «De original a Markdown»), §9 «Seguridad» (fila «Licencias») y §10 (fase 3: entregable y cómo se comprueba), `travel-agency/AGENTS.md` fila 3, `rag/AGENTS.md`, `travel-agency/.gitignore`. **Tema 5**: `05_rag_langchain/practica/README.md`, `docs/paso-01-inspeccion.md`, `docs/paso-02-hit-pagina.md` y `Ejercicios/rag-tenerife/utilidades.py` (`cargar_paginas`: el original no se toca, se conserva la numeración física y cada fragmento lleva `source` y `page`). **Tema 7**: `DropLab/documentos/` y `DropLab_sesion_2/practica/sesion_2/10_corpus.py` (qué fuentes entran y cuáles no). `database/data/aeropuertos.csv` (países de destino).

**Desvíos respecto al patrón de clase:**
- No hay en el repo un modelo de `SOURCES.md` ni de cómo reunir un corpus de varias fuentes (en clase el corpus es un solo PDF o una carpeta ya dada). Formato acordado con Mario: tabla Markdown con columna `Archivo` para cruzar cada fichero con su fila.
- Columna `SHA-256` y límite de 10 MB para git: acordados con Mario; no vienen de `PROYECTO.md`.

## Alcance

**Dentro**
- Descargar con `curl` desde las URL oficiales el conjunto mínimo de AC-2 y comprobar la licencia en el aviso legal de cada fuente; Mario revisa la tabla.
- `rag/corpus/SOURCES.md`: una fila por archivo con las columnas `Archivo` · `Título` · `URL` · `Descarga` · `Licencia` · `Carpeta` · `En git` · `SHA-256`.
- Reglas de `.gitignore` para las carpetas de uso privado y los archivos de más de 10 MB.
- Los comandos de comprobación apuntados en `rag/AGENTS.md`, para repetirlos cuando cambie el corpus.

**Fuera**
- Tests, scripts o módulos de Python: no hacen falta para un entregable de datos.
- Documentos de `empresa/` (TRAVEL-004).
- Conversión a Markdown y aviso de páginas sin texto (fase 4).
- BAAI/IndustryCorpus_travel, Wikivoyage y normativa autonómica de agencias de viajes.

## Criterios de aceptación

### Camino feliz

**AC-1 — Cada archivo del corpus tiene su fila completa**
- **Dado** `rag/corpus/` con los documentos descargados
- **Cuando** se compara la lista de archivos (`find rag/corpus -type f`, sin `.gitkeep` ni `SOURCES.md`) con la columna `Archivo` de `SOURCES.md`
- **Entonces** cada archivo aparece en exactamente una fila
- **Y** cada fila tiene las 8 columnas rellenas y `Descarga` con formato `AAAA-MM-DD`

**AC-2 — Está el conjunto mínimo acordado**
- **Dado** `SOURCES.md`
- **Cuando** Mario revisa sus filas
- **Entonces** aparecen, en `leyes/`, el Reglamento (CE) 261/2004, la Directiva (UE) 2015/2302 y el Reglamento (CE) 2027/97 de EUR-Lex en español y el RDL 1/2007 consolidado del BOE
- **Y** en `salud/`, una edición anterior a la vigente del Yellow Book (CDC)
- **Y** en `seguridad/`, al menos 2 páginas de EASA, las páginas de AESA de derechos del pasajero, equipaje y líquidos, y las recomendaciones de viaje de Exteriores de Francia, Países Bajos, Italia, Reino Unido, Estados Unidos, Portugal y Alemania
- **Y** en `general/`, un subconjunto de tabiji travel-safety-guides con esos 7 países

**AC-3 — Los originales están sin alterar**
- **Dado** los archivos del corpus presentes en disco
- **Cuando** se ejecuta `sha256sum -c` con las huellas de la columna `SHA-256`
- **Entonces** todos dan `OK`

### Casos límite

**AC-4 — Lo de uso privado no entra en git**
- **Dado** que las filas de AESA y Exteriores tienen la licencia `Solo uso privado`
- **Cuando** se ejecutan `git check-ignore rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores` y `git ls-files rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores`
- **Entonces** el primero devuelve las dos carpetas y el segundo no devuelve nada
- **Y** sus filas tienen `En git: no`

**AC-5 — Los archivos de más de 10 MB quedan fuera de git**
- **Dado** los archivos que devuelve `find rag/corpus -type f -size +10M` (p. ej. el Yellow Book)
- **Cuando** se pasa cada uno por `git check-ignore`
- **Entonces** todos están ignorados
- **Y** sus filas tienen `En git: no`

**AC-6 — La columna `En git` dice la verdad**
- **Dado** `SOURCES.md`
- **Cuando** se compara con `git ls-files rag/corpus`
- **Entonces** los archivos que salen son exactamente los de las filas con `En git: sí` (más `SOURCES.md` y los `.gitkeep`)

**AC-7 — Solo entran licencias claras**
- **Dado** `SOURCES.md`
- **Cuando** se revisa la columna `Licencia`
- **Entonces** cada valor es uno de estos: `Reutilización libre UE (Decisión 2011/833/UE)` · `Reutilización libre (aviso legal del BOE)` · `Dominio público (EE. UU.)` · `Reproducción autorizada citando la fuente (EASA)` · `CC BY 4.0` · `Solo uso privado`

### Errores

No aplica: no hay código que falle. Un documento cuya licencia no esté clara no se descarga ni se apunta (AC-7).

### No funcionales

Ninguno para este ticket.

## Definición de hecho

- [ ] Cada AC comprobado con la revisión o el comando que nombra
- [ ] La suite del proyecto sigue en verde (`uv run pytest`): el ticket no toca código
- [ ] `rag/AGENTS.md` (deja la fase 0: `SOURCES.md`, carpetas fuera de git y comandos de comprobación) y la fila 3 de `travel-agency/AGENTS.md` actualizados con lo que se siguió de clase y los desvíos
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- Lista cerrada de licencias de AC-7 sacada de la tabla de `PROYECTO.md` §4; AESA (prohibida la reproducción salvo citando) se trata como `Solo uso privado`, igual que Exteriores. TRAVEL-004 añade `Apache 2.0 (nuestros)`.
- `Descarga` en formato `AAAA-MM-DD`; `En git` con valores `sí` / `no`; las rutas de `Archivo` son relativas a `rag/corpus/`.
- 10 MB como límite para git (acordado con Mario), medido como lo mide `find -size +10M`.
- Del Yellow Book vale cualquier edición anterior a la vigente; se elige la que tenga PDF con texto.

**Preguntas abiertas**
- Qué 2-3 páginas concretas de EASA entran (equipaje, objetos peligrosos, derechos del pasajero…): se proponen al descargar y Mario las aprueba.
- Formato del subconjunto de tabiji: Parquet original filtrado o el Parquet completo fuera de git. Se decide al ver su tamaño real.
