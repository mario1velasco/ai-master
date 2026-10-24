"""Uso: python -m app.scripts.check_keys

Comprueba una a una las 3 API keys configuradas en .env, llamando al modelo
por defecto con un mensaje mínimo, y reporta cuáles funcionan.
"""

from anthropic import APIStatusError

from app.api_clients.anthropic_client import send_message
from app.config import ANTHROPIC_API_KEYS, DEFAULT_MODEL


def main() -> None:
    for index, api_key in enumerate(ANTHROPIC_API_KEYS, start=1):
        try:
            send_message(api_key=api_key, model=DEFAULT_MODEL, message="ping", max_tokens=8)
            print(f"API Key {index}: OK")
        except APIStatusError as error:
            print(f"API Key {index}: ERROR ({error.status_code})")


if __name__ == "__main__":
    main()
