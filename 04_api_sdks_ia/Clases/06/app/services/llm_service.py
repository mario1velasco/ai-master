import random

from anthropic import APIStatusError
from pydantic import BaseModel

from app import config
from app.api_clients.anthropic_client import (
    LLMResult,
    StructuredLLMResult,
    call_llm,
    call_llm_with_schema,
)
from app.domain.schemas import ConversationState
from app.llm.mock import mock_call_llm_with_schema
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SATURATION_STATUS_CODES = (429, 529)


def get_structured_llm_reply(
    *,
    prompt: str,
    model: str,
    schema: type[BaseModel],
    temperature: float,
    max_tokens: int,
    tool_name: str,
    tool_description: str,
    session_state: ConversationState | None = None,
    message: str | None = None,
) -> StructuredLLMResult:
    if config.USE_MOCK_LLM:
        return mock_call_llm_with_schema(session_state=session_state, message=message)

    keys_to_try = random.sample(config.ANTHROPIC_API_KEYS, len(config.ANTHROPIC_API_KEYS))
    last_error: APIStatusError | None = None
    for api_key in keys_to_try:
        try:
            return call_llm_with_schema(
                api_key=api_key,
                prompt=prompt,
                model=model,
                schema=schema,
                temperature=temperature,
                max_tokens=max_tokens,
                tool_name=tool_name,
                tool_description=tool_description,
                timeout=config.LLM_TIMEOUT_SECONDS,
            )
        except APIStatusError as error:
            if error.status_code not in _SATURATION_STATUS_CODES:
                raise
            logger.warning("Key saturada (status %s), rotando a la siguiente.", error.status_code)
            last_error = error

    if last_error is not None:
        raise last_error
    raise RuntimeError("No se pudo llamar al LLM, no hay claves configuradas.")


def get_llm_reply(*, prompt: str, model: str, temperature: float, max_tokens: int) -> LLMResult:
    keys_to_try = random.sample(config.ANTHROPIC_API_KEYS, len(config.ANTHROPIC_API_KEYS))
    last_error: APIStatusError | None = None
    for api_key in keys_to_try:
        try:
            return call_llm(
                api_key=api_key,
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=config.LLM_TIMEOUT_SECONDS,
            )
        except APIStatusError as error:
            if error.status_code not in _SATURATION_STATUS_CODES:
                raise
            logger.warning("Key saturada (status %s), rotando a la siguiente.", error.status_code)
            last_error = error

    if last_error is not None:
        raise last_error
    raise RuntimeError("No se pudo llamar al LLM, no hay claves configuradas.")
