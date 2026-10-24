from dataclasses import dataclass
import os
from pathlib import Path
import unicodedata
import yaml
from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    root: Path
    session06: Path
    llm_model: str = "gpt-4.1-mini"
    candidate_depth: int = 100
    context_k: int = 6
    context_tokens: int = 6500
    document_tokens: int = 1200
    max_output_tokens: int = 1200
    max_tool_calls: int = 2
    request_timeout: int = 45
    answer_cache: bool = True

    def __post_init__(self):
        if self.candidate_depth != 100:
            raise ValueError("Este ejercicio conserva 100 candidatos por rama.")
        if not 1 <= self.context_k <= 12 or not 1 <= self.max_tool_calls <= 3:
            raise ValueError("Contexto: 1–12 documentos; herramientas: 1–3 llamadas.")
        if not 512 <= self.context_tokens <= 16000 or not 128 <= self.document_tokens <= 2000:
            raise ValueError("Presupuesto de contexto fuera de límites.")
        if not 128 <= self.max_output_tokens <= 4000 or not 1 <= self.request_timeout <= 120:
            raise ValueError("Límites de generación no válidos.")

    @property
    def artifacts(self):
        return self.root / "artifacts" / "rag"


def project_root():
    return Path(__file__).resolve().parents[3]


def load_settings(root=None):
    root = Path(root or project_root()).resolve()
    local = {k: v for k, v in dotenv_values(root / ".env").items() if v}
    location = os.getenv("SESSION06_DIR") or local.get("SESSION06_DIR")
    if location:
        previous = Path(location).expanduser()
        previous = (root / previous).resolve() if not previous.is_absolute() else previous.resolve()
    else:
        matches = [p for p in root.parent.iterdir()
                   if unicodedata.normalize("NFC", p.name).casefold() in ("sesión 06", "sesión 6")]
        if not matches:
            raise FileNotFoundError("No se encuentra Sesión 06. Define SESSION06_DIR en el entorno o en .env.")
        previous = matches[0]
    inherited = {k: v for k, v in dotenv_values(previous / ".env").items() if v}
    for key, value in (inherited | local).items():
        os.environ.setdefault(key, value)
    parameters = yaml.safe_load((root / "config/rag.yaml").read_text())
    parameters["llm_model"] = os.getenv("RAG_LLM_MODEL", parameters["llm_model"])
    return Settings(root=root, session06=previous, **parameters)
