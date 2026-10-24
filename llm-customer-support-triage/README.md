# AI Customer Support Triage API

A FastAPI service that uses Claude (Anthropic) to triage incoming customer support
messages: it extracts a structured case state from free-text conversation, enforces
deterministic business rules on top of the model's output, and decides the next
operation — ask for a missing field, escalate to a human, or route into a workflow
(refund, delivery change, billing review, technical ticket...).

It's built as a **hybrid LLM system**: the model handles language understanding and
extraction, but every decision that matters (what's required, when to escalate, what
happens next) is deterministic code that the LLM cannot override.

## What this project demonstrates

- **Structured LLM outputs, not prompt-and-parse.** Responses are forced through
  Anthropic tool-calling (`tool_choice={"type": "tool", ...}`) and validated against a
  Pydantic schema — no regex/JSON scraping, no silent parsing failures.
- **LLM-as-untrusted-input.** The prompt explicitly tells the model to treat user
  messages as data, not instructions, and the state-merge logic ([`app/domain/business_rules.py`](app/domain/business_rules.py))
  refuses to let a proposed update erase already-known facts with empty values. Covered
  by a dedicated eval case for prompt injection ([`eval/eval_cases.yml`](eval/eval_cases.yml), `EVAL-005`).
- **LLM proposes, code disposes.** The model only ever produces a candidate state
  update and a reply message. Required-fields-per-case-type, human-escalation rules,
  and routing decisions live in plain Python functions with no I/O, fully unit-testable
  in isolation from the model ([`tests/test_business_rules.py`](tests/test_business_rules.py)).
- **Provider reliability.** Three API keys are rotated per request; on 429/529
  (rate-limited/overloaded) the client transparently retries with the next key
  ([`app/services/llm_service.py`](app/services/llm_service.py)) instead of failing the request.
- **Context engineering.** Conversation history is kept as a sliding window and
  auto-summarized past a configurable message count, so token cost doesn't grow
  unbounded on long cases ([`app/session/manager.py`](app/session/manager.py)).
- **Cost and observability by default.** Every LLM call is logged as a structured
  JSONL event with latency, token counts, estimated USD cost, and the prompt/schema/rules
  version that produced it ([`app/utils/observability.py`](app/utils/observability.py)) — enough to reconstruct
  "what changed" when behavior regresses.
- **Offline evaluation harness.** A golden dataset of multi-turn cases with expected
  final state/operation, runnable against either a deterministic mock or the real model,
  producing pass/fail + CSV/JSON reports ([`eval/`](eval/)) — regression testing for LLM behavior,
  not just code.
- **Deterministic mock mode.** A rule-based mock LLM ([`app/llm/mock.py`](app/llm/mock.py)) lets the full
  request flow run in tests and CI with zero API cost and zero non-determinism.
- **Clean layering.** Routes → services → domain (pure business logic) → API client.
  The only file that talks to Anthropic is [`app/api_clients/anthropic_client.py`](app/api_clients/anthropic_client.py); swapping
  LLM providers touches nothing else.

## How a request flows

1. `POST /cases/{case_id}/events` receives a message for a case.
2. The session's current state, summary, and recent messages are assembled into a prompt.
3. Claude returns a structured `ConversationUpdate` (new state + reply) via tool-calling.
4. The proposed state is merged into the existing state (existing facts win over blanks),
   then run through the business rules to compute missing fields, escalation, and the
   next operation.
5. The turn is persisted, logged (cost/latency/versions), and returned to the caller.

## Architecture

```
app/
├── main.py             # FastAPI routes: validation, HTTP error mapping, orchestration
├── config.py            # single source of truth for env vars + config.yml
├── dto.py                # API request/response schemas (Pydantic)
├── domain/
│   ├── schemas.py         # ConversationState / ConversationUpdate (LLM output contract)
│   └── business_rules.py  # pure functions: state merge, validation, next-operation routing
├── session/
│   ├── manager.py          # per-case conversation state, history, summarization, trace
│   └── store.py             # in-memory session store
├── llm/
│   ├── prompts.py           # prompt construction (context + summarization prompts)
│   └── mock.py                # deterministic rule-based LLM substitute for tests/CI
├── services/
│   ├── llm_service.py        # multi-key rotation, failover on 429/529, mock bypass
│   └── event_service.py        # orchestrates a full event: LLM call → rules → persistence → logging
├── api_clients/
│   └── anthropic_client.py    # only module that talks to the Anthropic API
├── utils/
│   ├── observability.py        # structured JSONL request logging + cost estimation
│   └── logger.py
└── scripts/
    └── check_keys.py            # verifies each configured API key independently

eval/
├── eval_cases.yml   # golden multi-turn cases with expected final state/operation
└── run_eval.py       # runs cases in mock or real mode, writes JSON/CSV reports

tests/                # pytest: API flow (mock mode) + business rules in isolation
```

## Tech stack

Python 3.11 · FastAPI · Pydantic v2 · Anthropic SDK (Claude, tool-calling) · pytest ·
pandas (eval reporting) · Docker · [uv](https://github.com/astral-sh/uv) for env/dependency management.

## Setup

```bash
make install          # uv venv .venv + uv pip install -r requirements.txt
cp .env.example .env  # fill in the 3 API keys (placeholders are fine if llm.use_mock_llm: true)
```

`app/config.py` requires all three `ANTHROPIC_API_KEY_1/2/3` env vars even in mock mode.
Behavior — model, temperature, token limits, mock toggle, context window, cost rates —
lives in [`config.yml`](config.yml), not in `.env`:

```yaml
llm:
  temperature: 0.0
  max_tokens: 700
  model: claude-haiku-4-5-20251001
  timeout_seconds: 30
  use_mock_llm: false
```

## Run

```bash
make dev   # uvicorn --reload, http://127.0.0.1:8100
make run   # without --reload
```

Interactive API docs at `http://127.0.0.1:8100/docs`.

## Endpoints

```text
GET    /health
GET    /cases
POST   /cases/{case_id}/events
GET    /cases/{case_id}/state
GET    /cases/{case_id}/trace
DELETE /cases/{case_id}
GET    /demo/stream
```

## Testing

```bash
make test          # pytest, always runs in mock mode — no API cost, no flakiness
make check-keys    # verifies each of the 3 configured API keys individually
```

## Evaluation (golden dataset)

```bash
make eval        # mock mode, no cost — behavioral regression check
make eval-real    # against the real provider
```

Writes `outputs/eval_results.json`, `outputs/eval_results.csv`, and `outputs/eval_summary.json`
with per-case pass/fail and an overall pass rate.

## Docker

```bash
make docker-build
make docker-run
```

or manually:

```bash
docker build -t triage-api-local .
docker run --rm --env-file .env -p 8100:8100 triage-api-local
```

The image is self-contained: no dependency on anything outside this repository.
