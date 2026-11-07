# Mocking

Mock **only at the boundaries you don't own or can't make deterministic**. Everything inside them runs for real.

| Mock / fake it | Don't mock it |
|---|---|
| LLM providers: Anthropic in triage, Ollama in travel-agency | Your own modules and functions, even across files |
| Network and external HTTP APIs | Pydantic models and DTOs: build real ones |
| The clock, when a value depends on it (`time`, `datetime.now`, `perf_counter`) | DuckDB in memory: real, fast and isolated |
| Randomness (seed it or inject it) | The triage session store: reset it with `clear_sessions()` |
| Environment and secrets (`monkeypatch.setenv`) | The filesystem: use `tmp_path` |

If a test needs to mock one of your own modules to be fast, the seam is probably wrong: test lower, or inject the slow dependency.

## How, in this repo

**Triage LLM.** `config.USE_MOCK_LLM = True` before importing `app.main`, and fake API keys in the environment, exactly as `tests/test_api.py` does. The mock (`app/llm/mock.py`) is deterministic: it extracts the order id with a regex and classifies by keywords. If a test needs a model answer the mock can't produce, extend the mock (agree it in the checkpoint) rather than patching inside the service.

**Travel-agency LLM.** Inject the client, or replace it at the seam with a small fake that returns a fixed answer with the same type as the real one. From phase 10 on, prefer **saved real outputs** (`PROYECTO.md`: *salidas reales guardadas como base del mock de los tests*) loaded as fixtures, so the fake answers look like the model's.

```python
from dataclasses import dataclass


@dataclass(slots=True)
class FakeLlm:
    """Responde siempre lo mismo y guarda lo que le preguntaron."""

    answer: str
    prompts: list[str]

    def chat(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer


def test_agent_answers_from_sql_result() -> None:
    llm = FakeLlm(answer='{"tool": "sql", "question": "reservas canceladas"}', prompts=[])

    answer = ask_agent("¿Cuántas reservas canceladas tengo?", llm=llm)

    assert answer.tool == "sql"
```

**Never a real call in tests.** No test reaches Anthropic or Ollama, not even "just one". If the `.env` has real keys, tests must not read them: set fake ones with `monkeypatch.setenv` or at module import, as triage does.

## Tools

- **`monkeypatch` over `unittest.mock.patch`**: it undoes itself at the end of the test, and works for attributes, environment variables and `sys.path`.
- **Patch where the name is looked up**, not where it is defined: if `event_service` does `from app.llm import client`, patch `app.services.event_service.client`.
- **Prefer fakes with real behavior to `Mock` with `assert_called_once_with`**: asserting calls couples the test to the implementation. Assert the outcome; check a call only when the call *is* the behavior (e.g. "an event is written once").
- **Latency and time:** assert `latency_ms >= 0` or a value range, or monkeypatch the clock. Never `sleep` in a test.
