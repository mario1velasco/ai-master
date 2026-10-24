import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

default_model = "claude-haiku-4-5-20251001"

_ENV_VARS = ("ANTHROPIC_API_KEY_1", "ANTHROPIC_API_KEY_2", "ANTHROPIC_API_KEY_3")
_missing = [name for name in _ENV_VARS if not os.environ.get(name)]
if _missing:
    raise RuntimeError(
        f"Faltan variables de entorno obligatorias en .env: {', '.join(_missing)}. "
        "Copia .env.example a .env y rellena las 3 API keys."
    )
ANTHROPIC_API_KEYS = [os.environ[name] for name in _ENV_VARS]

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yml"


def _load_app_config() -> dict:
    if not _CONFIG_PATH.exists():
        raise RuntimeError(f"config.yml no encontrado en {_CONFIG_PATH}")
    return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))


APP_CONFIG = _load_app_config()

LLM_MODEL = APP_CONFIG["llm"].get("model", default_model)
LLM_TIMEOUT_SECONDS = int(APP_CONFIG["llm"].get("timeout_seconds", 30))
USE_MOCK_LLM = bool(APP_CONFIG["llm"].get("use_mock_llm", False))
