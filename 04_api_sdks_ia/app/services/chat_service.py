import random

from anthropic import APIStatusError

from app.api_clients.anthropic_client import send_message
from app.config import ANTHROPIC_API_KEYS
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SATURATION_STATUS_CODES = (429, 529)


def get_chat_reply(message: str, model: str, max_tokens: int) -> str:
    keys_to_try = random.sample(ANTHROPIC_API_KEYS, len(ANTHROPIC_API_KEYS))
    last_error: APIStatusError | None = None

    for api_key in keys_to_try:
        try:
            return send_message(api_key=api_key, model=model, message=message, max_tokens=max_tokens)
        except APIStatusError as error:
            if error.status_code not in _SATURATION_STATUS_CODES:
                raise
            logger.warning("Key saturada (status %s), rotando a la siguiente.", error.status_code)
            last_error = error

    if last_error is not None:
        raise last_error
    else:
        raise RuntimeError("No se pudo enviar el mensaje, no hay claves configuradas.")
