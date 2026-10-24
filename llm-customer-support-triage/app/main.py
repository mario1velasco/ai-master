import time
from collections.abc import Generator

from anthropic import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app import config
from app.dto import (
    CaseStateResponse,
    EventRequest,
    EventResponse,
    HealthResponse,
    TraceResponse,
)
from app.services import event_service
from app.session.store import delete_session, get_session, list_case_ids

app = FastAPI(title=config.APP_CONFIG["app"]["name"], version=config.APP_CONFIG["app"]["version"])


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=config.APP_CONFIG["app"]["name"],
        app_version=config.APP_CONFIG["app"]["version"],
        deployment_environment=config.APP_CONFIG["app"]["deployment_environment"],
        model_configured=bool(config.LLM_MODEL),
        api_key_configured=len(config.ANTHROPIC_API_KEYS) == 3,
        use_mock_llm=config.USE_MOCK_LLM,
        prompt_version=config.APP_CONFIG["versions"]["prompt_version"],
        schema_version=config.APP_CONFIG["versions"]["schema_version"],
        rules_version=config.APP_CONFIG["versions"]["rules_version"],
    )


@app.get("/cases")
def list_cases() -> dict:
    return {"case_ids": list_case_ids()}


@app.post("/cases/{case_id}/events", response_model=EventResponse)
def process_event(case_id: str, request: EventRequest) -> EventResponse:
    try:
        return event_service.process_event(case_id=case_id, request=request)
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail="LLM provider rate limit exceeded.") from exc
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="LLM provider timeout.") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="Could not connect to LLM provider.") from exc
    except APIStatusError as exc:
        raise HTTPException(status_code=502, detail=f"LLM provider returned an error: {exc.status_code}") from exc
    except ValueError as exc:
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
