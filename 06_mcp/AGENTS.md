# AGENTS.md — Módulo "Integración con herramientas y MCP"

## De qué va este curso

Este repositorio contiene los materiales y ejercicios del módulo **06 · Integración con herramientas y MCP**, parte del [Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica) de EBIS Business Techschool.

El hilo conductor del módulo es: partiendo de un LLM "pelado" (que solo predice texto), construir progresivamente todo lo necesario para que se convierta en un agente capaz de usar herramientas, mantener contexto y actuar de forma fiable — primero "a mano" (harness propio, function calling manual) y más adelante usando el estándar **MCP (Model Context Protocol)** para conectar herramientas y fuentes de contexto de forma interoperable.

Cada carpeta numerada en la raíz es un **tema** del módulo, con su propio material (PDFs de teoría, enunciados de ejercicios) y proyectos de código:

- `01-agents-harness/`: qué es un LLM, la era de los agentes, el Agent Harness (bucle ReAct, gestión de contexto/historial, tools, permisos, subagentes) — la base conceptual sobre la que se apoya MCP. Incluye un ejercicio práctico (EBIS-CLI) con TODOs por resolver.
- `02-mcp/`: Model Context Protocol (MCP) — el problema M×N, arquitectura cliente/servidor, JSON-RPC, handshake vs. stateless, el SDK `mcp` de Python (servidor y cliente). Incluye un ejercicio práctico (EBIS-CLI conectado a un servidor MCP de calendario) con TODOs por resolver.
- `03-skills/`: Agent Skills (`SKILL.md`, carga por capas, skills vs. tools/MCP) y Decision Models (Jev de TypeSafe: Choice/Score/Noul, routing de modelos). Material de referencia sin ejercicio con TODOs: una skill de presentaciones (`presentacion-open/`), EBIS-CLI con Jev (`ebis-cli-decision-model/`) y cinco skills propias: dividir audios largos (`audio-split/`), transcribirlos a texto (`audio-decoder/`) resumir textos a `.md` y PDF (`text-resume/`) transcribir imágenes a `.md` (`img-to-text/`) y una orquestadora que encadena las cuatro de audios, imágenes y resumen (`media-resume/`).
- *(los siguientes temas se añaden aquí a medida que se incorporan al repo — mantén esta lista al día)*

## Documentación de cada tema

Cada carpeta de tema mantiene dos documentos con roles distintos:
- **`README.md`**: explica de qué trata el tema; pensado para que lo lea un humano (Mario) y entienda el contenido y los materiales.
- **`AGENTS.md`**: guía operativa para un agente (Claude Code u otro) que trabaje en esa carpeta — estructura, qué tocar y qué no, cómo ejecutar el código, dónde están los ejercicios pendientes.

Este archivo (`AGENTS.md` en la raíz) es el punto de entrada general del repositorio. Los `AGENTS.md` de cada tema añaden el detalle específico de esa carpeta y tienen prioridad sobre este cuando haya conflicto.

## Mantenimiento de la documentación

Cada vez que modifiques algo en el repositorio (código, materiales, estructura de carpetas), comprueba si algún `README.md` o `AGENTS.md` afectado —el de la raíz y/o el del tema concreto— se ha quedado desactualizado, y actualízalo en el mismo cambio.

- Antes de escribir, analiza el alcance real del cambio: si es puntual (un dato, un TODO resuelto, un fichero nuevo), edita solo esas líneas — no reescribas secciones enteras ni generes ruido innecesario en el diff.
- Si el cambio es lo bastante grande como para que mantener la estructura actual del documento genere más ruido que claridad (se añade un tema nuevo, cambia la organización del módulo, se reestructura un ejercicio), entonces sí merece la pena replantear esa sección antes de tocarla, en lugar de ir parcheando encima.
- Si no hay nada que actualizar, no toques los docs "porque sí".
