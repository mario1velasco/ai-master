import os
import time
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

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
    TraceResponse,
)
from business_rules import apply_business_rules, determine_next_operation, merge_state
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from llm_client import call_llm, call_llm_with_schema
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
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

client = Anthropic(
    api_key=LLM_API_KEY,
    timeout=LLM_TIMEOUT_SECONDS,
) if LLM_API_KEY else None

app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=config["app"]["name"],
        model_configured=bool(LLM_MODEL),
        api_key_configured=bool(LLM_API_KEY),
    )


@app.get("/cases")
def list_cases() -> dict:
    # ! sesion_store.py -> list_case_ids. Trae la lista de ids de las conversaciones
    return {"case_ids": list_case_ids()}


@app.post("/cases/{case_id}/events", response_model=EventResponse)
def process_event(case_id: str, request: EventRequest) -> EventResponse:
    if client is None or not LLM_MODEL:
        raise HTTPException(
            status_code=500,
            detail="LLM client is not configured. Check LLM_API_KEY and LLM_MODEL.",
        )

    # ! sesion_store.py -> get_or_create_session -> SessionManager. Esto es para que se puedan guardar los datos de las conversaciones
    session = get_or_create_session(case_id)

    try:
        prompt = build_context_prompt(
            session=session,
            user_message=request.message,
            config=config,
        )

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

        # ! IMP: estudiar que hace merge_state y apply_business_rules
        merged_state = merge_state(
            existing=session.state,
            proposed=update.updated_state,
        )
        state = apply_business_rules(merged_state)
        operation = determine_next_operation(state)

        # ! SessionManager -> add_message. Añade un mensaje del usuario al diccionario
        session.add_message("user", request.message)
        
        # ! IMPORTANTE UPDATE STATE
        # ! IMPORTANTE UPDATE STATE
        session.update_state(state)
        # ! IMPORTANTE UPDATE STATE
        # ! IMPORTANTE UPDATE STATE

        # ! SessionManager -> add_message. Añade un mensaje del asistente al diccionario
        session.add_message("assistant", update.assistant_message)

        summarized = False
        if session.should_summarize(config["context"]["summarize_after_messages"]):
            keep_last = config["context"]["keep_last_messages_after_summary"]
            old_messages = session.messages[:-keep_last]

            summary_prompt = build_summary_prompt(
                existing_summary=session.summary,
                messages_to_summarize=old_messages,
            )

            summary_result = call_llm(
                client=client,
                prompt=summary_prompt,
                model=LLM_MODEL,
                temperature=0.0,
                max_tokens=250,
            )

            # ! SessionManager -> compress_history. Compreme la conversacion y la guarda en el diccionario
            session.compress_history(
                summary=summary_result.text,
                keep_last_messages=keep_last,
            )
            summarized = True

        trace_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": request.event_type,
            "message": request.message,
            "metadata": request.metadata,
            "assistant_message": update.assistant_message,
            "operation": operation,
            "state": state.model_dump(mode="json"),
            "summarized": summarized,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        }

        # ! IMPORTANTE ADD TRACE EVENT
        # ! IMPORTANTE ADD TRACE EVENT
        session.add_trace_event(trace_event)
        # ! IMPORTANTE ADD TRACE EVENT
        # ! IMPORTANTE ADD TRACE EVENT

        return EventResponse(
            case_id=case_id,
            event_type=request.event_type,
            assistant_message=update.assistant_message,
            operation=operation,
            state=state,
            summarized=summarized,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            model=result.model,
        )

    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail="LLM provider rate limit exceeded.") from exc

    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="LLM provider timeout.") from exc

    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="Could not connect to LLM provider.") from exc

    except APIStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider returned an error: {exc.status_code}",
        ) from exc

    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/cases/{case_id}/state", response_model=CaseStateResponse)
def read_case_state(case_id: str) -> CaseStateResponse:
    # ! sesion_store.py -> get_session -> session_manager.SessionManager. Trae la conversacion de la session_id
    session = get_session(case_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    # ! SessionManager -> to_snapshot. Trae los datos de la conversacion y los convierte en un diccionario
    snapshot = session.to_snapshot()

    return CaseStateResponse(
        case_id=case_id,
        state=session.state,
        summary=snapshot["summary"],
        messages=snapshot["messages"],
        trace_size=snapshot["trace_size"],
    )


@app.get("/cases/{case_id}/trace", response_model=TraceResponse)
def read_case_trace(case_id: str) -> TraceResponse:
    # ! sesion_store.py -> get_session -> session_manager.SessionManager. Trae la conversacion de la session_id
    session = get_session(case_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    return TraceResponse(case_id=case_id, trace=session.trace)


@app.delete("/cases/{case_id}")
def reset_case(case_id: str) -> dict:
    # ! sesion_store.py -> delete_session.SessionManager. Borra la conversacion de la session_id
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
            time.sleep(3)

    return StreamingResponse(generate(), media_type="text/plain")
