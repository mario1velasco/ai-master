# AGENTS.md — Módulo "IA Agéntica y automatización basada en agentes"

## De qué va este curso

Este repositorio contiene los materiales y ejercicios del módulo **08 · IA Agéntica y automatización basada en agentes** (Tema 8), parte del [Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica) de EBIS Business Techschool.

El hilo conductor del módulo es un único caso: el **agente de operaciones de Lumen Shop**, una tienda online de cosmética simulada. A lo largo de seis sesiones se construye el mismo sistema, de menos a más: empieza como un bucle agéntico de ~80 líneas en Python sin frameworks y termina como un sistema multiagente integrado en un flujo empresarial con aprobación humana. Parte de lo visto en el Tema 6 (`../06_mcp/`: agente, tool calling, MCP) y lo construye "por dentro".

Las seis sesiones del tema:

1. Del LLM al agente: anatomía y arquitectura.
2. Razonar y actuar: ReAct y patrones de planificación.
3. Herramientas desde la perspectiva del agente (LangGraph, APIs externas, MCP, aprobación humana).
4. Memoria, contexto y estado.
5. Sistemas multiagente.
6. Agentes en producción e integración empresarial.

## Estructura del repositorio

- `Tema8_Trabajo_previo_a_clase.pdf`: qué preparar antes de cada sesión (instalación, deberes, lecturas, tiempos).
- `Tema8_Deberes_y_lecturas.pdf`: enunciados de los deberes (nivel base + reto) y lecturas de las seis sesiones.
- `tema8-agentes/`: **el repositorio de código del tema**, compartido por todas las sesiones. Tiene su propio `README.md` y `GUIA_INSTALACION.md`.
  - `comun/`: conexión con el modelo (`llm.py`, `modelo_lc.py`), datos simulados de la tienda (`tienda.py`), herramientas compartidas, utilidades.
  - `sesion1/` … `sesion6/`: demos de cada sesión, cada una con su `README.md` (demos + enunciado de deberes).
- Carpetas numeradas de sesión con la teoría (PDF de la sesión) y su `explicacion.md`:
  - `01-del-llm-al-agente/`: sesión 1 — workflow vs. agente, los cinco patrones de workflow, el bucle agéntico, componentes del agente, niveles de autonomía, multiplicación de errores, cuándo no usar un agente. Su código está en `tema8-agentes/sesion1/`.
  - `02-ReAct-patrone-planificacion/`: sesión 2 — ReAct frente a tool calling, diseño de herramientas, bucles y parada, plan-and-execute, reflexión, comparar estrategias. Tiene el `Resumen Clase 2-7 Tema 8.pdf` (no hay PDF de diapositivas: el `explicacion-08.md` se completa con capturas de clase) y `video/` con la grabación (no versionada; descargada con la skill `campus-video-download`). Su código está en `tema8-agentes/sesion2/`.
  - `03-tools/`: sesión 3 — herramientas desde la perspectiva del agente (LangGraph, APIs externas, MCP, aprobación humana). No hay PDF de diapositivas: su `explicacion-08.md` está hecho con capturas de clase, en estilo sencillo y centrado en la idea principal. Su sección 7 queda abierta hasta recibir el repo `tema8-mlflow`. Su código está en `tema8-agentes/sesion3/`.
  - *(las siguientes sesiones se añaden aquí a medida que se incorporan al repo — mantén esta lista al día)*

## Documentación de cada sesión

Cada carpeta de sesión mantiene documentos con roles distintos:
- **`explicacion.md`**: explicación larga y didáctica de todo el contenido de la sesión (PDF de teoría + código de `tema8-agentes/sesionN/`), en lenguaje sencillo y sin dar nada por sabido. Pensada para que la lea un humano (Mario). Todo lo que afirma debe venir del PDF o del código real; los ejemplos propios se marcan como ilustrativos.
- **`AGENTS.md`** (si existe): guía operativa para un agente que trabaje en esa carpeta. Tiene prioridad sobre este cuando haya conflicto.

Este archivo (`AGENTS.md` en la raíz) es el punto de entrada general del repositorio.

## Cómo ejecutar el código

Entorno: Python ≥ 3.10, entorno virtual y dependencias de `tema8-agentes/requirements.txt`. Modelo por defecto: **Ollama en local con `qwen2.5:7b`** (opcionalmente `nomic-embed-text` para embeddings en la sesión 4). Toda la conexión usa la API compatible con OpenAI y se configura en `.env` (copiar de `.env.example`: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`); para pasar a un proveedor en la nube solo se edita `.env`, no el código.

```bash
cd tema8-agentes
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python comprobar_entorno.py      # debe terminar con «Todo listo para el Tema 8»
python -m sesion1.agente_minimo "¿Hay stock de crema hidratante?"
```

Las demos se ejecutan **siempre desde `tema8-agentes/` y como módulo** (`python -m sesionN.script`), porque importan `comun`.

## Reglas al trabajar en el código

- `comun/tienda.py` es la "base de datos" simulada de Lumen Shop. `consultar_transportista` lanza siempre `ConnectionError` **a propósito** (simula una API caída para provocar bucles en clase): no lo "arregles".
- Los deberes de cada sesión están en el `README.md` de `tema8-agentes/sesionN/` y en `Tema8_Deberes_y_lecturas.pdf`. Si el usuario pide ayuda con un deber, guíale; no lo resuelvas entero salvo que lo pida explícitamente.
- `soluciones/` aparece en el README del repo pero aún no existe: se publica tras la corrección en clase.
- No subas `.env` (está en `.gitignore`).

## Mantenimiento de la documentación

Cada vez que modifiques algo en el repositorio (código, materiales, estructura de carpetas), comprueba si algún `README.md`, `AGENTS.md` o `explicacion.md` afectado —el de la raíz y/o el de la sesión concreta— se ha quedado desactualizado, y actualízalo en el mismo cambio.

- Antes de escribir, analiza el alcance real del cambio: si es puntual (un dato, un deber resuelto, un fichero nuevo), edita solo esas líneas — no reescribas secciones enteras ni generes ruido innecesario en el diff.
- Si el cambio es lo bastante grande como para que mantener la estructura actual del documento genere más ruido que claridad (se añade una sesión nueva, cambia la organización del módulo, se reestructura un ejercicio), entonces sí merece la pena replantear esa sección antes de tocarla, en lugar de ir parcheando encima.
- Si no hay nada que actualizar, no toques los docs "porque sí".
