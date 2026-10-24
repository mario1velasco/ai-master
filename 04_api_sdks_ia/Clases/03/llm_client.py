from dataclasses import dataclass
from time import perf_counter
from typing import Generic, Type, TypeVar

from pydantic import BaseModel

# ! Uso de genericos para tipos de resultados de llamada a la API
T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResult:
    text: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int


@dataclass
class StructuredLLMResult(Generic[T]):
    object: T
    raw_tool_input: dict
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int


def call_llm(client, prompt: str, model: str, temperature: float, max_tokens: int) -> LLMResult:
    start = perf_counter()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    latency_ms = int((perf_counter() - start) * 1000)

    return LLMResult(
        text=text,
        model=model,
        latency_ms=latency_ms,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


def call_llm_with_schema(
    client,
    prompt: str,
    model: str,
    schema: Type[T],
    temperature: float,
    max_tokens: int,
    tool_name: str,
    tool_description: str,
) -> StructuredLLMResult[T]:
    start = perf_counter()

    tool = {
        "name": tool_name,
        "description": tool_description,
        "input_schema": schema.model_json_schema(),
    }

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": prompt}],
    )

    latency_ms = int((perf_counter() - start) * 1000)

    tool_input = None
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            tool_input = block.input

    if tool_input is None:
        raise ValueError("Expected tool_use block was not returned.")

    validated_object = schema(**tool_input)

    return StructuredLLMResult(
        object=validated_object,
        raw_tool_input=tool_input,
        model=model,
        latency_ms=latency_ms,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
