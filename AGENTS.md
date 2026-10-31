# AGENTS.md — Repositorio `ebis`

## De qué va

Material de Mario para el **[Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica)** de EBIS Business Techschool: teoría (PDFs), demos, ejercicios y prácticas de cada tema, más algunos proyectos propios. Todo en **español**, salvo algún proyecto personal.

## Estructura

Cada carpeta es **independiente**: su propio entorno (`.venv`), sus dependencias, su `.env` y, en muchos casos, su propio repo git.

### Temas del máster (carpetas `NN_nombre`)

| Carpeta | Tema |
|---|---|
| `01_Introduccion_al_ML_DL_LLMs/` | Intro a ML, deep learning, NLP y LLMs |
| `03_API_Integracion_servicios/` | APIs REST, OAuth, rate limits, webhooks |
| `04_api_sdks_ia/` | APIs y SDKs de proveedores de IA |
| `05_rag_langchain/` | RAG con LangChain (clases + práctica) |
| `06_mcp/` | Agentes, harness, tools, MCP y Agent Skills |
| `07_llm_open_source/` | LLMs open source en local (Ollama) |
| `08_ia_agentica_automatiz_agentes/` | IA agéntica: del bucle agéntico a sistemas multiagente (caso Lumen Shop) |

(No hay tema 02 en el repo.)

### Otras carpetas

| Carpeta | Qué es |
|---|---|
| `Ejercicios/` | Ejercicios propios fuera de temario (p. ej. `rag-tenerife/`) |
| `Skills-mario/` | Colección de skills propias para Claude Code (audio, imágenes, texto, presentaciones) |
| `llm-customer-support-triage/` | Proyecto personal: API FastAPI que usa Claude para triar mensajes de soporte (en inglés) |
| `travel-agency/` | Proyecto personal (fase 1 hecha: contratos de métricas y telemetría; uv workspace): agente de agencia de viajes con text-to-SQL afinado + RAG, todo open source en local, API FastAPI. Diseño en `PROYECTO.md` |

## Reglas importantes

- **Cada carpeta tiene su propio `.env`. No crees nunca un `.env` en la raíz** ni lo compartas entre carpetas: daría conflictos de claves y configuraciones. Si falta, se copia del `.env.example` de esa carpeta.
- No subas ni muestres el contenido de ningún `.env`.
- Ejecuta el código **desde dentro de su carpeta**, con su propio entorno.
- **Siempre que escribas, edites o revises código Python**, carga antes la skill `python-developer` (en `.claude/skills/python-developer/`). Si choca con lo que ya hace una carpeta (versión de Python, `requirements.txt` en vez de `pyproject.toml`, sin layout `src/`, etc.), manda lo que ya existe en la carpeta: no migres la estructura por tu cuenta.
- **Commits a nombre de Mario**: sin `Co-Authored-By` ni ninguna mención a la IA en el mensaje de commit ni en las PR.
- Antes de trabajar en una carpeta, lee su `AGENTS.md`, `CLAUDE.md` o `README.md` si existe: tienen el detalle y **prioridad** sobre este archivo.

## Mantener esta documentación

Se irán añadiendo cursos y carpetas nuevas. Cuando aparezca, cambie de nombre o desaparezca una carpeta de primer nivel, actualiza las tablas de **Estructura** en el mismo cambio. Edita solo lo necesario; si no ha cambiado nada, no toques el archivo.

Lo mismo con el `AGENTS.md` de cada carpeta: si haces un cambio **importante** dentro de ella, actualízalo en el mismo cambio. Tú decides si lo es, con este criterio:

- **Sí actualizar**: algo que deja desfasado lo que dice ese `AGENTS.md`. Por ejemplo, material de clase nuevo con tecnologías nuevas, una subcarpeta o práctica nueva, otra forma de instalar o ejecutar, dependencias o variables de `.env` nuevas, o un cambio de arquitectura.
- **No actualizar**: cambios menores que no afectan a lo documentado, como cambiar una función, arreglar un bug, refactorizar o retocar textos.

Si la carpeta no tiene `AGENTS.md` y el cambio es importante, menciónalo al terminar en lugar de crearlo por tu cuenta.
