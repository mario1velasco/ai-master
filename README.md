# ai-master

Mi material del **[Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica)** de EBIS Business Techschool: apuntes, demos, ejercicios y prácticas de cada tema, junto con algunos proyectos propios.

El recorrido va de los fundamentos de machine learning y LLMs hasta agentes de IA que usan herramientas, MCP y sistemas multiagente.

## Contenido

### Temas del máster

| Carpeta | Tema |
|---|---|
| [`01_Introduccion_al_ML_DL_LLMs`](01_Introduccion_al_ML_DL_LLMs) | Introducción a machine learning, deep learning, NLP y LLMs |
| [`03_API_Integracion_servicios`](03_API_Integracion_servicios) | APIs REST, OAuth, rate limits y webhooks |
| [`04_api_sdks_ia`](04_api_sdks_ia) | APIs y SDKs de proveedores de IA |
| [`05_rag_langchain`](05_rag_langchain) | RAG (generación aumentada por recuperación) con LangChain |
| [`06_mcp`](06_mcp) | Agentes, tool calling, Model Context Protocol (MCP) y Agent Skills |
| [`07_llm_open_source`](07_llm_open_source) | LLMs de código abierto en local con Ollama |
| [`08_ia_agentica_automatiz_agentes`](08_ia_agentica_automatiz_agentes) | IA agéntica: del bucle agéntico a sistemas multiagente |

### Otros proyectos

| Carpeta | Qué es |
|---|---|
| [`Ejercicios`](Ejercicios) | Ejercicios propios fuera del temario (p. ej. un RAG sobre Tenerife) |
| [`Skills-mario`](Skills-mario) | Skills para Claude Code: transcribir audio, describir imágenes, resumir textos, crear presentaciones |
| [`llm-customer-support-triage`](llm-customer-support-triage) | API con FastAPI que usa Claude para clasificar y encaminar mensajes de soporte al cliente |

## Cómo usarlo

Cada carpeta es **independiente**, con sus propias dependencias y su propia configuración. Para ejecutar algo:

1. Entra en la carpeta que te interese y lee su `README.md` (si lo tiene).
2. Crea su entorno virtual e instala sus dependencias.
3. Copia su `.env.example` a `.env` y rellena tus claves.

> No hay un `.env` global: cada carpeta tiene el suyo, porque las claves y la configuración cambian de un tema a otro.

## Tecnologías

Python, OpenAI y Anthropic (Claude) SDKs, LangChain, LangGraph, MCP, Ollama, FastAPI, PyTorch y TensorFlow, entre otras.
