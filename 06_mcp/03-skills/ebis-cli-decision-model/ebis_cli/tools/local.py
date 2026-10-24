"""Tools locales de archivos, búsqueda y desarrollo dentro del workspace."""

import asyncio
import os
import signal
from pathlib import Path

from ..settings import MAX_COMMAND_SECONDS, MAX_TOOL_OUTPUT_CHARS, WORK_DIR


WORKSPACE = WORK_DIR
IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".ebis_cli"}
RESERVED_NAMES = {".ebis_cli"}


def local_path(name: str) -> Path:
    root = WORKSPACE.resolve()
    path = (root / name).resolve()
    if path != root and root not in path.parents:
        raise ValueError("La ruta debe permanecer dentro de la carpeta de trabajo.")
    relative_parts = path.relative_to(root).parts if path != root else ()
    if any(
        part in RESERVED_NAMES or part.startswith(".env") for part in relative_parts
    ):
        raise ValueError("La ruta pertenece a datos reservados del runtime.")
    return path


def _ignored(path: Path) -> bool:
    try:
        relative = path.relative_to(WORKSPACE)
    except ValueError:
        return True
    return any(
        part in IGNORED_DIRS or part.startswith(".env") for part in relative.parts
    )


def list_files() -> str:
    files: list[str] = []
    for folder, subfolders, names in os.walk(WORKSPACE):
        subfolders[:] = [
            name
            for name in subfolders
            if name not in IGNORED_DIRS and not name.startswith(".env")
        ]
        for name in names:
            path = Path(folder) / name
            if not _ignored(path):
                files.append(path.relative_to(WORKSPACE).as_posix())
    return "\n".join(sorted(files)) if files else "La carpeta de trabajo está vacía."


def read_file(path: str) -> str:
    file_path = local_path(path)
    if not file_path.is_file():
        return f"No existe el archivo: {path}"
    content = file_path.read_text(encoding="utf-8")
    return _truncate(content)


def write_file(path: str, content: str) -> str:
    file_path = local_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"Guardado: {file_path.relative_to(WORKSPACE).as_posix()} ({len(content)} caracteres)."


def make_directory(path: str) -> str:
    directory = local_path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return f"Directorio listo: {directory.relative_to(WORKSPACE).as_posix()}"


def search_files(query: str, glob: str) -> str:
    if not query:
        return "La búsqueda está vacía."
    if not glob or ".." in Path(glob).parts or Path(glob).is_absolute():
        raise ValueError(
            "El patrón glob debe ser relativo y no puede salir del workspace."
        )

    matches: list[str] = []
    for path in WORKSPACE.rglob("*"):
        if not path.is_file() or _ignored(path) or not path.match(glob):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if query.casefold() in line.casefold():
                snippet = line.strip()[:240]
                matches.append(
                    f"{path.relative_to(WORKSPACE).as_posix()}:{line_number}: {snippet}"
                )
                if len(matches) >= 100:
                    matches.append(
                        "…resultados limitados a las primeras 100 coincidencias."
                    )
                    return "\n".join(matches)
    return "\n".join(matches) if matches else "No se encontraron coincidencias."


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    """Termina un comando cancelado y recoge el proceso para no dejarlo huérfano."""
    if process.returncode is not None and os.name == "nt":
        return
    try:
        if os.name == "nt":
            process.terminate()
        else:
            os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass
    try:
        await asyncio.wait_for(process.wait(), timeout=1.5)
        return
    except asyncio.TimeoutError:
        pass
    try:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass
    try:
        await asyncio.wait_for(process.wait(), timeout=2)
    except asyncio.TimeoutError:
        pass


async def run_command(command: str, timeout_seconds: int) -> str:
    if not command.strip():
        return "El comando está vacío."
    timeout_seconds = max(1, min(int(timeout_seconds), MAX_COMMAND_SECONDS))
    process = await asyncio.create_subprocess_shell(
        command,
        cwd=str(WORKSPACE),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **({"start_new_session": True} if os.name != "nt" else {}),
    )
    stdout_task = asyncio.create_task(
        _read_bounded(process.stdout, MAX_TOOL_OUTPUT_CHARS)
    )
    stderr_task = asyncio.create_task(
        _read_bounded(process.stderr, MAX_TOOL_OUTPUT_CHARS)
    )
    try:
        await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
        exit_code = process.returncode
    except asyncio.CancelledError:
        await _stop_process(process)
        stdout_task.cancel()
        stderr_task.cancel()
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
        raise
    except asyncio.TimeoutError:
        await _stop_process(process)
        exit_code = process.returncode
        timeout_note = (
            f"\nTiempo límite alcanzado ({timeout_seconds} s); proceso terminado."
        )
    else:
        timeout_note = ""
    try:
        (stdout, stdout_truncated), (stderr, stderr_truncated) = await asyncio.wait_for(
            asyncio.gather(stdout_task, stderr_task), timeout=3
        )
    except asyncio.CancelledError:
        await _stop_process(process)
        stdout_task.cancel()
        stderr_task.cancel()
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
        raise
    except asyncio.TimeoutError:
        stdout_task.cancel()
        stderr_task.cancel()
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
        stdout, stderr = b"", b""
        stdout_truncated = stderr_truncated = True
    truncation_note = (
        "\n…salida del proceso limitada por el harness."
        if stdout_truncated or stderr_truncated
        else ""
    )

    output = (
        f"Comando: {command}\nDirectorio: {WORKSPACE}\nCódigo de salida: {exit_code}"
        f"\n--- stdout ---\n{stdout.decode(errors='replace')}"
        f"\n--- stderr ---\n{stderr.decode(errors='replace')}"
        f"{truncation_note}{timeout_note}"
    )
    return _truncate(output)


async def _read_bounded(
    stream: asyncio.StreamReader | None, limit: int
) -> tuple[bytes, bool]:
    if stream is None:
        return b"", False
    collected = bytearray()
    was_truncated = False
    while chunk := await stream.read(8192):
        remaining = limit - len(collected)
        if remaining > 0:
            collected.extend(chunk[:remaining])
        if len(chunk) > remaining:
            was_truncated = True
    return bytes(collected), was_truncated


def count_words(text: str) -> str:
    return f"Número de palabras: {len(text.split())}"


def _truncate(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT_CHARS:
        return text
    return text[:MAX_TOOL_OUTPUT_CHARS] + "\n…salida truncada por el harness."


TOOLS = [
    {
        "type": "function",
        "name": "list_files",
        "description": "Lista los archivos del workspace omitiendo secretos y datos internos del agente.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Lee un archivo de texto dentro del workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Crea o reemplaza un archivo de texto dentro del workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_files",
        "description": "Busca un texto en archivos del workspace y devuelve rutas, líneas y fragmentos.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "glob": {
                    "type": "string",
                    "description": "Patrón relativo, por ejemplo **/*.py",
                },
            },
            "required": ["query", "glob"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "make_directory",
        "description": "Crea un directorio dentro del workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "run_command",
        "description": "Ejecuta un comando de desarrollo desde el workspace y devuelve stdout, stderr y código de salida.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Tiempo máximo de ejecución, hasta 120 segundos.",
                },
            },
            "required": ["command", "timeout_seconds"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "count_words",
        "description": "Cuenta las palabras separadas por espacios en blanco de un texto.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


async def dispatch_local_tool(name: str, arguments: dict) -> str:
    functions = {
        "list_files": list_files,
        "read_file": read_file,
        "write_file": write_file,
        "search_files": search_files,
        "make_directory": make_directory,
        "run_command": run_command,
        "count_words": count_words,
    }
    try:
        function = functions[name]
        result = function(**arguments)
        if asyncio.iscoroutine(result):
            result = await result
        return _truncate(str(result))
    except Exception as error:
        return f"Error de herramienta {name}: {error}"
