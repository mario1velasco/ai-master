from dataclasses import dataclass
from time import perf_counter

from anthropic import Anthropic
from pydantic import BaseModel


@dataclass
class LLMResult:
    text: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    input_chars: int
    output_chars: int


@dataclass
class StructuredLLMResult:
    object: BaseModel
    raw_tool_input: dict
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int


def _usage_value(usage, name: str) -> int:
    return int(getattr(usage, name, 0) or 0)


def call_llm(api_key: str, prompt: str, model: str, temperature: float, max_tokens: int, timeout: float | None = None) -> LLMResult:
    client = Anthropic(api_key=api_key, timeout=timeout)
    start = perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = int((perf_counter() - start) * 1000)
    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    text = "\n".join(text_blocks).strip()
    return LLMResult(
        text=text,
        model=model,
        latency_ms=latency_ms,
        input_tokens=_usage_value(response.usage, "input_tokens"),
        output_tokens=_usage_value(response.usage, "output_tokens"),
        input_chars=len(prompt),
        output_chars=len(text),
    )


def call_llm_with_schema(api_key: str, prompt: str, model: str, schema: type[BaseModel], temperature: float, max_tokens: int, tool_name: str, tool_description: str, timeout: float | None = None) -> StructuredLLMResult:
    client = Anthropic(api_key=api_key, timeout=timeout)
    tool = {"name": tool_name, "description": tool_description, "input_schema": schema.model_json_schema()}
    start = perf_counter()
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
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            tool_input = block.input
            break
    if tool_input is None:
        raise ValueError(f"Model did not return the expected tool call: {tool_name}")
    validated_object = schema(**tool_input)
    return StructuredLLMResult(
        object=validated_object,
        raw_tool_input=tool_input,
        model=model,
        latency_ms=latency_ms,
        input_tokens=_usage_value(response.usage, "input_tokens"),
        output_tokens=_usage_value(response.usage, "output_tokens"),
    )
