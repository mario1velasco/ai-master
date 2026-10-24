from anthropic import Anthropic
from anthropic.types import TextBlock


def send_message(api_key: str, model: str, message: str, max_tokens: int) -> str:
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": message}],
    )

    text_blocks = [block.text for block in response.content if isinstance(block, TextBlock)]
    if not text_blocks:
        raise ValueError("El modelo no ha devuelto ningún bloque de texto.")

    return "".join(text_blocks)
