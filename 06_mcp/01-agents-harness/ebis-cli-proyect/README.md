# ebis-cli-proyect

Agente de línea de comandos en Python para practicar la integración de tools con la API de OpenAI. El proyecto parte de una implementación funcional de las herramientas de archivos y del loop del agente; la práctica consiste en ampliar sus herramientas y completar la gestión del historial.

## Funcionalidades

- Interfaz de terminal interactiva basada en Textual.
- Lectura, escritura y listado de archivos en la carpeta de trabajo.
- Tools descritas mediante esquemas JSON y conectadas a un dispatcher local.
- Loop con la Responses API de OpenAI.
- Historial de conversación mantenido en memoria durante la ejecución.

## Requisitos

- Python 3.11 o posterior.
- [uv](https://docs.astral.sh/uv/) para instalar dependencias y ejecutar el proyecto.
- Una clave de API de OpenAI.

## Instalación y ejecución

Desde la carpeta del repositorio:

```bash
uv sync
```

Copia `.env.example` como `.env` y añade tu clave en `OPENAI_API_KEY`. Puedes conservar `OPENAI_MODEL` o cambiarlo por un modelo disponible para tu cuenta. En Linux:

```bash
cp .env.example .env
```

Inicia la aplicación:

```bash
uv run python -m ebis_cli.app
```

`uv sync` prepara el entorno virtual local e instala las dependencias declaradas en `pyproject.toml`. `uv run` ejecuta el comando dentro de ese entorno.

## Práctica

El enunciado completo está en [`enunciado.md`](enunciado.md). Los puntos principales son:

1. Añadir las tools `count_words` y `calculate_total`, incluidos sus esquemas y su registro en el dispatcher.
2. Corregir el envío del historial a la API de OpenAI.
3. Compactar el historial al superar el límite de palabras configurado.

El proyecto incluye el andamiaje y marca las dos zonas de trabajo con comentarios `TODO`.

## Uso

- Escribe un objetivo en español para conversar con el agente.
- Usa `/tools` para mostrar las herramientas anunciadas al modelo.
- Usa `/help` para ver los comandos disponibles.
- Usa `/clear` para limpiar la vista y `/exit` para cerrar la aplicación.

## Estructura

```text
ebis-cli-proyect/
├── ebis_cli/
│   ├── agent.py       # Loop del agente y llamadas a la Responses API
│   ├── context.py     # Carga de .env e instrucciones AGENTS.md
│   ├── tools.py       # Funciones locales, esquemas y dispatcher
│   └── app.py         # Interfaz de terminal
├── .env.example
├── enunciado.md
└── pyproject.toml
```

## Referencias

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Responses API: estado de conversación](https://developers.openai.com/api/docs/guides/conversation-state)
- [Function calling](https://developers.openai.com/api/docs/guides/function-calling)
