# TRAVEL-004 · Redactar los documentos propios de Viajes Nimbo

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`rag/corpus/empresa/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-07 |
| Etiquetas | rag, corpus, empresa, fase-3, documentos |

## Historia de usuario

**Como** responsable del RAG de Viajes Nimbo, **quiero** la documentación que tendría una agencia de viajes real en España, coherente con la base de datos y con casos difíciles metidos a propósito, **para que** el agente pueda responder y citar las políticas de la agencia, y la evaluación pueda comprobar que usa la versión vigente, aplica la política propia cuando mejora la ley y no obedece instrucciones escondidas en un documento.

## Contexto

`rag/corpus/empresa/` está vacía. `PROYECTO.md` §4 «Documentos propios de Viajes Nimbo» fija la lista de documentos por subcarpeta, los casos que se meten a propósito y que cada documento lleve `titulo`, `version`, `vigente_desde`, `ambito` y `publico`. Con Mario se acordó escribir esa cabecera al estilo de DropLab (texto libre, como `politica_reembolsos.md`) con una línea más para ámbito y público. Es la segunda mitad de la fase 3; el corpus externo y `SOURCES.md` van en TRAVEL-003, del que depende.

Es un ticket **de documentos, sin código**: cada criterio se comprueba revisando los documentos o con `grep`. Las cabeceras se leerán con las expresiones de `leer_md` cuando se trocee (fase 8); si alguna está mal, se verá allí.

**Referencias leídas:** `travel-agency/PROYECTO.md` §4, §9 «Seguridad» (inyección en documentos, filtro por `publico`) y §10 (fase 3), `travel-agency/AGENTS.md` fila 3. **Tema 7**: `07_llm_open_source/clase_01/Ejercicios/DropLab/documentos/politica_reembolsos.md` (modelo de documento), `clase_02/DropLab_sesion_2/data/documentos/{propuesta_pack4_borrador.md, calendario_comercial_aprobado.md}` (borrador y versión aprobada que «sustituye a» la anterior), `clase_03/DropLab_sesion_3/data/documentos/{aviso_obras.md, diario_operaciones_abril.md}`, `clase_02/DropLab_sesion_2/practica/sesion_2/10_corpus.py` (`leer_md`: código con `Documento ([A-Z0-9-]+)`, primera fecha `dd/mm/aaaa`, estado por `Versión`/`Estado`, `Responsable`, secciones `## `, regla «sustituye a X»). **Tema 5**: `Ejercicios/rag-tenerife/utilidades.py` (cita con documento y página). `database/data/*.csv` (valores que los documentos deben respetar).

**Desvíos respecto al patrón de clase:**
- Línea `Ámbito: … · Público: cliente|interno`, que DropLab no tiene: la pide `PROYECTO.md` §4 para filtrar después (no citar el manual interno a un cliente).
- Licencia `Apache 2.0 (nuestros)` en `SOURCES.md` para textos propios, como dice `PROYECTO.md` §4 (en clase los documentos no llevan licencia).

## Alcance

**Dentro**
- Los 24 documentos de la lista de `PROYECTO.md` §4 en Markdown, en `corporativo/`, `legal/`, `politicas/`, `viajero/`, `atencion/`, `interno/` y `pruebas/`, más la versión antigua de la política de cancelación en `politicas/historico/`.
- Los casos a propósito: política que mejora la ley, políticas que dependen de la BBDD, versión sustituida y documento trampa con instrucción inyectada.
- Sus filas en `SOURCES.md`, ampliando la lista de licencias de TRAVEL-003 con `Apache 2.0 (nuestros)`.
- Contenido propuesto por Claude y aprobado por Mario documento a documento.

**Fuera**
- Tests, scripts o módulos de Python: no hacen falta para un entregable de documentos.
- Corpus externo y formato de `SOURCES.md` (TRAVEL-003).
- Leer la cabecera como metadatos de cada fragmento, trocear y filtrar por `publico` (fase 8).
- Conversión (los `.md` se copian tal cual en la fase 4).
- Revisión legal real del contenido: es una agencia ficticia.
- Versiones en otros idiomas.

## Criterios de aceptación

### Camino feliz

**AC-1 — Están todos los documentos de la lista**
- **Dado** `rag/corpus/empresa/`
- **Cuando** se listan sus archivos `.md` (`find rag/corpus/empresa -name '*.md'`)
- **Entonces** hay uno por cada documento de la tabla de `PROYECTO.md` §4 (24) en su subcarpeta, más la versión antigua de la política de cancelación en `politicas/historico/` (25 en total)

**AC-2 — Cada documento tiene la cabecera completa**
- **Dado** cualquier documento de `empresa/`
- **Cuando** se revisan sus primeras líneas
- **Entonces** tiene un título `# Viajes Nimbo · <título>`, una línea `Documento <CÓDIGO> · Versión <n> · Vigente desde <dd/mm/aaaa>`, una línea `Responsable: <área>` y una línea `Ámbito: <subcarpeta> · Público: cliente|interno`
- **Y** al menos una sección `## `

**AC-3 — Cada documento tiene su fila en `SOURCES.md`**
- **Dado** los documentos de `empresa/`
- **Cuando** se comparan con las filas de `SOURCES.md` (como en el AC-1 de TRAVEL-003)
- **Entonces** cada documento tiene una fila con licencia `Apache 2.0 (nuestros)`, `En git: sí`, `URL: —` y `SHA-256: —`

### Casos límite

**AC-4 — La política de reembolsos mejora el plazo legal**
- **Dado** la política de cancelación y reembolsos vigente
- **Cuando** se lee
- **Entonces** fija el reembolso en 7 días
- **Y** cita el plazo legal de 14 días de la Directiva (UE) 2015/2302

**AC-5 — Los documentos usan los valores de la base de datos**
- **Dado** `database/data/`
- **Cuando** se revisan estos documentos
- **Entonces** el programa de fidelización define exactamente los niveles de `clientes.nivel_fidelidad` (`basico`, `plata`, `oro`)
- **Y** la política de cancelación distingue los tipos de `reservas.tipo` (`paquete`, `solo_vuelo`)
- **Y** la política de equipaje da franquicia para cada clase de `reservas_tramos.clase` (`turista`, `business`)
- **Y** la de pagos nombra los 4 métodos de `pagos.metodo` (tarjeta, bizum, PayPal, transferencia)
- **Y** la relación con proveedores nombra exactamente las 6 aerolíneas de `aerolineas.csv`

**AC-6 — La versión antigua queda sustituida por la vigente**
- **Dado** las dos versiones de la política de cancelación
- **Cuando** se revisan sus cabeceras
- **Entonces** la vigente contiene «sustituye a <código de la antigua>»
- **Y** su `Vigente desde` es posterior al de la antigua
- **Y** las dos fijan plazos o penalizaciones distintos

**AC-7 — Los códigos son únicos**
- **Dado** todas las cabeceras de `empresa/`
- **Cuando** se extraen los códigos (`grep -rhoE 'Documento [A-Z0-9-]+' rag/corpus/empresa | sort | uniq -d`)
- **Entonces** no sale ninguno repetido
- **Y** todo «sustituye a X» nombra un código que existe en `empresa/`

**AC-8 — El documento trampa lleva una instrucción inyectada**
- **Dado** el documento de `pruebas/`
- **Cuando** se lee
- **Entonces** contiene una instrucción dirigida al modelo que empieza por «Ignora las normas anteriores»
- **Y** su cabecera tiene `Ámbito: pruebas`

**AC-9 — Solo los documentos internos son de público interno**
- **Dado** todas las cabeceras de `empresa/`
- **Cuando** se busca `Público: interno` (`grep -rl 'Público: interno' rag/corpus/empresa`)
- **Entonces** salen exactamente los documentos de `interno/`, y todos los demás dicen `Público: cliente`

**AC-10 — La FAQ tiene entre 40 y 60 preguntas**
- **Dado** el documento de preguntas frecuentes
- **Cuando** se cuentan sus secciones `### ` (una por pregunta)
- **Entonces** hay entre 40 y 60, cada una con su respuesta debajo

### Errores

No aplica: no hay código que falle. Lo que no cumpla un criterio se corrige en el documento antes de cerrar el ticket.

### No funcionales

**AC-11 — Ningún dato de contacto es real**
- **Dado** todos los documentos de `empresa/`
- **Cuando** se buscan correos y webs (`grep -rhoE '[[:alnum:]._-]+@[[:alnum:].-]+|https?://[^ )]+' rag/corpus/empresa`)
- **Entonces** todos están en un dominio reservado para ejemplos (`example.com` o `*.example`)

## Definición de hecho

- [ ] Cada AC comprobado con la revisión o el comando que nombra
- [ ] Contenido de cada documento aprobado por Mario
- [ ] La suite del proyecto sigue en verde (`uv run pytest`): el ticket no toca código
- [ ] `rag/AGENTS.md` (formato de cabecera de `empresa/`) y la fila 3 de `travel-agency/AGENTS.md` (fase 3 terminada, lo que se siguió de clase y los desvíos) actualizados
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos** (Mario pidió crear el ticket sin otra ronda de preguntas; revisarlos)
- Las cifras del contenido (penalizaciones por antelación, ventajas por nivel, franquicias, horarios) no son requisitos del ticket: Claude las propone y Mario las aprueba documento a documento, como los repartos de TRAVEL-001.
- `Ámbito` es el nombre de la subcarpeta de primer nivel de `empresa/` (la versión antigua, en `politicas/historico/`, tiene `Ámbito: politicas`); fechas en `dd/mm/aaaa`, como en DropLab.
- Los documentos propios no llevan huella (`SHA-256: —`) ni URL (`URL: —`): son nuestros y cambian mientras se redactan. `—` solo se admite con licencia `Apache 2.0 (nuestros)`.
- El documento trampa es de público `cliente`, para que llegue a la búsqueda en los dos modos y se pueda comprobar la defensa.
- Datos registrales y título-licencia de agencia ficticios y reconocibles como tales.
- La versión antigua es solo de la política de cancelación (el caso de `PROYECTO.md` pide una).

**Preguntas abiertas**
- ~~¿La versión antigua vive junto a la vigente en `politicas/` o en una subcarpeta propia?~~ Resuelto: en `politicas/historico/` (Mario, 2026-11-07).
- ~~¿Fechas de vigencia alineadas con las reservas generadas en `database/data/`?~~ Resuelto: sí. Las fechas `Vigente desde` caen dentro del periodo de las reservas generadas (06/09/2024–31/10/2026) o antes; la fecha en que la versión antigua pasa a la vigente la aprueba Mario al redactarla.
