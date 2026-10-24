import json
import os
from pathlib import Path

from .context import WORK_DIR

WORKSPACE = WORK_DIR


def local_path(name: str) -> Path:
    root = WORKSPACE.resolve()
    path = (root / name).resolve()
    if path != root and root not in path.parents:
        raise ValueError("La ruta debe permanecer dentro de la carpeta de trabajo")
    if path.name.startswith(".env") or path.name == ".agent-memory.json":
        raise ValueError("El archivo está reservado por el runtime")
    return path


IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules"}


def list_files() -> str:
    files = []
    for folder, subfolders, names in os.walk(WORKSPACE):
        subfolders[:] = [name for name in subfolders if name not in IGNORED_DIRS]
        for name in names:
            if name.startswith(".env") or name == ".agent-memory.json":
                continue
            path = Path(folder) / name
            files.append(path.relative_to(WORKSPACE).as_posix())
    return "\n".join(sorted(files)) if files else "La carpeta de trabajo está vacía"


def read_file(path: str) -> str:
    file_path = local_path(path)
    if not file_path.exists():
        return f"No existe: {path}"
    return file_path.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    file_path = local_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"Guardado: {path}"


TOOLS = [
    {
        "type": "function",
        "name": "list_files",
        "description": "Lista los archivos de la carpeta de trabajo actual.",
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Lee un archivo de la carpeta de trabajo actual.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Crea o reemplaza un archivo dentro de la carpeta de trabajo actual.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"], "additionalProperties": False},
        "strict": True,
    },
]


def dispatch_tool(name: str, arguments: dict) -> str:
    functions = {"list_files": list_files, "read_file": read_file, "write_file": write_file}
    try:
        return functions[name](**arguments)
    except Exception as error:
        return f"Error de herramienta: {error}"
