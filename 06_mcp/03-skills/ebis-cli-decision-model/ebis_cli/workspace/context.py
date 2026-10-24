from dotenv import load_dotenv

from ..settings import CODE_DIR, WORK_DIR


def load_environment():
    load_dotenv(WORK_DIR / ".env")


def load_instructions(default_instructions):
    sections = [default_instructions]
    seen = set()
    files = [
        ("Instrucciones del código", CODE_DIR / "AGENTS.md"),
        ("Instrucciones de la carpeta de trabajo", WORK_DIR / "AGENTS.md"),
    ]

    for label, path in files:
        path = path.resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            sections.append(f"{label} ({path}):\n{text}")

    return "\n\n".join(sections)
