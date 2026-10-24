import os

from dotenv import load_dotenv

load_dotenv()

_ENV_VARS = ("ANTHROPIC_API_KEY_1", "ANTHROPIC_API_KEY_2", "ANTHROPIC_API_KEY_3")

_missing = [name for name in _ENV_VARS if not os.environ.get(name)]
if _missing:
    raise RuntimeError(
        f"Faltan variables de entorno obligatorias en .env: {', '.join(_missing)}. "
        "Copia .env.example a .env y rellena las 3 API keys."
    )

ANTHROPIC_API_KEYS = [os.environ[name] for name in _ENV_VARS]
