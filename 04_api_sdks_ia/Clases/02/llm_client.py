# llm_client.py
from dataclasses import dataclass
from time import perf_counter

from anthropic.types import TextBlock


@dataclass
class LLMResult:
    text: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    input_chars: int
    output_chars: int


def call_llm(
    client,
    prompt: str,
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 500,
) -> LLMResult:
    start = perf_counter()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    text_blocks = [block.text for block in response.content if isinstance(block, TextBlock)]
    text = "".join(text_blocks)

    if not text:
        raise Exception("LLM returned empty text content")

    latency_ms = int((perf_counter() - start) * 1000)

    return LLMResult(
        text=text,
        model=model,
        latency_ms=latency_ms,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        input_chars=len(prompt),
        output_chars=len(text),
    )
