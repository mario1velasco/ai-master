from dataclasses import dataclass


class ModelResponseError(RuntimeError):
    pass


@dataclass
class ModelTurn:
    text: str
    calls: list[dict]
    output: list[dict]
    input_tokens: int = 0
    output_tokens: int = 0


class OpenAIModel:
    def __init__(self, settings, client=None):
        from openai import OpenAI
        self.settings = settings
        self.client = client or OpenAI(timeout=settings.request_timeout, max_retries=2)

    def turn(self, messages, instructions, tools=None, force_search=False, *, response_format=None):
        options = {}
        if tools:
            options = {"tools": tools, "parallel_tool_calls": False,
                       "tool_choice": {"type": "function", "name": "search_library"} if force_search else "auto"}
        if response_format is not None:
            options["text"] = {"format": response_format}
        response = self.client.responses.create(model=self.settings.llm_model, input=messages,
            instructions=instructions, max_output_tokens=self.settings.max_output_tokens,
            store=False, **options)
        if response.status != "completed":
            raise ModelResponseError("La generación no terminó; revisa el presupuesto de salida o la disponibilidad del modelo.")
        output = [item.model_dump(exclude_none=True) for item in response.output]
        if any(part.get("type") == "refusal" for item in output
               for part in item.get("content", [])):
            raise ModelResponseError("El modelo rechazó la solicitud de generación.")
        if response_format is not None and not (response.output_text or "").strip():
            raise ModelResponseError("El modelo devolvió una respuesta estructurada vacía.")
        calls = [item for item in output if item["type"] == "function_call"]
        return ModelTurn(response.output_text, calls, output,
                         response.usage.input_tokens, response.usage.output_tokens)
