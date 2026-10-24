import os
import time
from pathlib import Path
from typing import Generator

import yaml
from anthropic import (
    Anthropic,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from api_models import (
    CaseStateResponse,
    EventRequest,
    EventResponse,
    HealthResponse,
    RequestMetrics,
    TraceResponse,
)
from business_rules import apply_business_rules, determine_next_operation, merge_state
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from llm_client import call_llm, call_llm_with_schema
from mock_llm import mock_call_llm_with_schema
from observability import build_observability_event, estimate_cost, write_jsonl
from prompts import build_context_prompt, build_summary_prompt
from schemas import ConversationUpdate
from session_store import (
    delete_session,
    get_or_create_session,
    get_session,
    list_case_ids,
)


def load_config() -> dict:
    config_path = Path("config.yml")
    if not config_path.exists():
        raise RuntimeError("config.yml was not found.")
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


load_dotenv()
config = load_config()
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mock-triage-model")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

client = None
if not USE_MOCK_LLM and LLM_API_KEY:
    client = Anthropic(api_key=LLM_API_KEY, timeout=LLM_TIMEOUT_SECONDS)

app = FastAPI(title=config["app"]["name"], version=config["app"]["version"])

def _log_error(case_id: str, request: EventRequest, error_type: str, status_code: int, prompt: str | None) -> None:
    session = get_or_create_session(case_id)
    obs_event = build_observability_event(
        case_id=case_id,
        event_type=request.event_type,
        message=request.message,
        operation="no_state_update",
        state=session.state.model_dump(mode="json"),
        model=LLM_MODEL,
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        status="error",
        error_type=f"{status_code}_{error_type}",
        config=config,
        prompt=prompt,
    )
    session.add_trace_event(obs_event)
    write_jsonl(config["observability"]["request_log_path"], obs_event)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=config["app"]["name"],
        app_version=config["app"]["version"],
        deployment_environment=config["app"]["deployment_environment"],
        model_configured=bool(LLM_MODEL),
        api_key_configured=bool(LLM_API_KEY),
        use_mock_llm=USE_MOCK_LLM,
        prompt_version=config["versions"]["prompt_version"],
        schema_version=config["versions"]["schema_version"],
        rules_version=config["versions"]["rules_version"],
    )


@app.get("/cases")
def list_cases() -> dict:
    return {"case_ids": list_case_ids()}


@app.post("/cases/{case_id}/events", response_model=EventResponse)
def process_event(case_id: str, request: EventRequest) -> EventResponse:
    if not USE_MOCK_LLM and client is None:
        raise HTTPException(status_code=500, detail="LLM client is not configured. Check LLM_API_KEY or set USE_MOCK_LLM=true.")

    session = get_or_create_session(case_id)
    prompt = build_context_prompt(session=session, user_message=request.message, config=config)

    try:
        if USE_MOCK_LLM:
            result = mock_call_llm_with_schema(session_state=session.state, message=request.message)
        else:
            result = call_llm_with_schema(
                client=client,
                prompt=prompt,
                model=LLM_MODEL,
                schema=ConversationUpdate,
                temperature=config["llm"]["temperature"],
                max_tokens=config["llm"]["max_tokens"],
                tool_name="update_conversation_state",
                tool_description="Update the case state and produce the next assistant message.",
            )

        update = result.object
        merged_state = merge_state(existing=session.state, proposed=update.updated_state)
        state = apply_business_rules(merged_state)
        operation = determine_next_operation(state)

        session.add_message("user", request.message)
        session.update_state(state)
        session.add_message("assistant", update.assistant_message)

        summarized = False
        if not USE_MOCK_LLM and session.should_summarize(config["context"]["summarize_after_messages"]):
            keep_last = config["context"]["keep_last_messages_after_summary"]
            old_messages = session.messages[:-keep_last]
            summary_prompt = build_summary_prompt(existing_summary=session.summary, messages_to_summarize=old_messages)
            summary_result = call_llm(client=client, prompt=summary_prompt, model=LLM_MODEL, temperature=0.0, max_tokens=250)
            session.compress_history(summary=summary_result.text, keep_last_messages=keep_last)
            summarized = True

        cost = estimate_cost(input_tokens=result.input_tokens, output_tokens=result.output_tokens, config=config)
        obs_event = build_observability_event(
            case_id=case_id,
            event_type=request.event_type,
            message=request.message,
            operation=operation,
            state=state.model_dump(mode="json"),
            model=result.model,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            status="success",
            config=config,
            prompt=prompt,
        )
        session.add_trace_event(obs_event)
        write_jsonl(config["observability"]["request_log_path"], obs_event)

        return EventResponse(
            case_id=case_id,
            event_type=request.event_type,
            assistant_message=update.assistant_message,
            operation=operation,
            state=state,
            summarized=summarized,
            metrics=RequestMetrics(
                model=result.model,
                latency_ms=result.latency_ms,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                estimated_cost=cost,
                currency=config["cost"]["currency"],
            ),
            prompt_version=config["versions"]["prompt_version"],
            schema_version=config["versions"]["schema_version"],
            rules_version=config["versions"]["rules_version"],
        )

    except RateLimitError as exc:
        _log_error(case_id, request, "rate_limit", 429, prompt)
        raise HTTPException(status_code=429, detail="LLM provider rate limit exceeded.") from exc
    except APITimeoutError as exc:
        _log_error(case_id, request, "timeout", 504, prompt)
        raise HTTPException(status_code=504, detail="LLM provider timeout.") from exc
    except APIConnectionError as exc:
        _log_error(case_id, request, "connection_error", 503, prompt)
        raise HTTPException(status_code=503, detail="Could not connect to LLM provider.") from exc
    except APIStatusError as exc:
        _log_error(case_id, request, "provider_error", 502, prompt)
        raise HTTPException(status_code=502, detail=f"LLM provider returned an error: {exc.status_code}") from exc
    except ValueError as exc:
        _log_error(case_id, request, "invalid_structured_output", 502, prompt)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/cases/{case_id}/state", response_model=CaseStateResponse)
def read_case_state(case_id: str) -> CaseStateResponse:
    session = get_session(case_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    snapshot = session.to_snapshot()
    return CaseStateResponse(case_id=case_id, state=session.state, summary=snapshot["summary"], messages=snapshot["messages"], trace_size=snapshot["trace_size"])


@app.get("/cases/{case_id}/trace", response_model=TraceResponse)
def read_case_trace(case_id: str) -> TraceResponse:
    session = get_session(case_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return TraceResponse(case_id=case_id, trace=session.trace)


@app.delete("/cases/{case_id}")
def reset_case(case_id: str) -> dict:
    deleted = delete_session(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Case not found.")
    return {"case_id": case_id, "deleted": True}


@app.get("/demo/stream")
def demo_stream() -> StreamingResponse:
    def generate() -> Generator[str, None, None]:
        chunks = [
            "Step 1/4 · Receiving event...\n",
            "Step 2/4 · Building context...\n",
            "Step 3/4 · Calling LLM...\n",
            "Step 4/4 · Validating response and deciding next operation...\n",
            "\nDone. Streaming improves perceived latency, but the workflow still needs validation.\n",
        ]
        for chunk in chunks:
            yield chunk
            time.sleep(0.8)
    return StreamingResponse(generate(), media_type="text/plain")
