# EBIS-CLI Harness v8

**Concepto:** Permisos y control de capacidades.

## Qué cambia en esta versión

`LEAD_PERMISSIONS` y `WORKER_PERMISSIONS` declaran los nombres de tools permitidos. `tools_for` filtra los esquemas que recibe el modelo; `execute` vuelve a validar cada llamada.
El agente principal puede delegar, verificar y usar memoria. El subagente solo recibe lectura y escritura de archivos y listado. Es un control del harness, no un aislamiento del sistema operativo.

Esta versión hereda el contexto de v4 para el principal: desde el cuarto run, `build_context(goal)` selecciona el historial relevante. Esa selección no ejecuta tools ni cambia permisos. El subagente sigue recibiendo únicamente la tarea delegada y sus propias respuestas de tools.

## Recorrido de una petición

1. `ebis_cli/agent.py` reúne objetivo, historial disponible, instrucciones y esquemas de tools.
2. El SDK de OpenAI envía esos datos al modelo.
3. Si el modelo pide una tool, `dispatch_tool` ejecuta la función local con los argumentos recibidos.
4. El resultado vuelve al contexto y el loop continúa o termina según las reglas de esta versión.

## Mapa del código

- `ebis_cli/agent.py`: loop del agente y coordinación de respuestas y tools.
- `ebis_cli/context.py`: distingue el proyecto de código de la carpeta actual; carga `.env` y `AGENTS.md`.
- `ebis_cli/tools.py`: implementaciones locales, esquemas disponibles para el modelo y despacho de llamadas.
- `AGENTS.md`: instrucciones por defecto para el agente cuando trabaja con este proyecto.
- `.env.example` y `pyproject.toml`: ejemplo de configuración y dependencias de UV.

La capa visual se considera una caja negra en este material; el recorrido didáctico se centra en el agente y el harness.

## Cómo añadir una tool

Una tool tiene tres partes: función Python, esquema de argumentos para el modelo y registro en el dispatcher. La función devuelve texto para que el resultado pueda volver al contexto.

1. En `ebis_cli/tools.py`, implementa la operación. Si lee o escribe rutas, pásalas por `local_path` para impedir salir de la carpeta de trabajo.
2. Añade el esquema a `TOOLS`: nombre igual al de la función, descripción clara y parámetros. Indica los campos obligatorios y conserva `strict: True`.
3. Esta versión extiende el dispatcher por capas: añade el caso en el último `dispatch_tool` de `tools.py`, antes de delegar en el dispatcher anterior.
4. En `ebis_cli/agent.py`, agrega el nombre a los permisos de cada rol que deba usar la tool. El esquema se filtra y el permiso vuelve a validarse en ejecución.

Si falta el esquema, el modelo no sabrá que la tool existe. Si falta el registro, la llamada no llegará a la función.

## Carpeta de trabajo, AGENTS.md y API key

`WORK_DIR` es el directorio desde el que se inicia el proceso. `CODE_DIR` se obtiene desde la ubicación del paquete. Así `uv run --project "$CODE_DIR"` usa el código y sus dependencias sin cambiar la carpeta en la que trabajan las tools.

`context.py` carga `.env` desde `WORK_DIR`. Pon allí `OPENAI_API_KEY`; `OPENAI_MODEL` es opcional. El agente combina sus instrucciones por defecto, el `AGENTS.md` del proyecto de código y el `AGENTS.md` raíz de la carpeta de trabajo. No busca instrucciones en subcarpetas.

`tools.py` usa `WORK_DIR` como raíz y bloquea rutas que intenten salir de ella. Las tools normales reservan `.env` y `.agent-memory.json`; el listado omite también carpetas de dependencias.

## Ejecución en Linux

Desde la carpeta del proyecto de código:

    cd "$HOME/ruta/ebis-cli-harness-v8"
    cp .env.example .env
    # Añade OPENAI_API_KEY a .env.
    uv sync
    uv run python -m ebis_cli.app

Desde una carpeta de trabajo X distinta:

    cd "$HOME/proyectos/mi-proyecto"
    CODE_DIR="$HOME/ruta/ebis-cli-harness-v8"
    cp "$CODE_DIR/.env.example" .env
    # Añade OPENAI_API_KEY al .env de X.
    uv run --project "$CODE_DIR" python -m ebis_cli.app

El segundo comando mantiene X como carpeta actual. No hace falta copiar el código del agente a X ni definir `PYTHONPATH`.
