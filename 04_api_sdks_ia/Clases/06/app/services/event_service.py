from anthropic import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

from app import config
from app.domain.business_rules import (
    apply_business_rules,
    determine_next_operation,
    merge_state,
)
from app.domain.schemas import ConversationUpdate
from app.dto import EventRequest, EventResponse, RequestMetrics
from app.llm.prompts import build_context_prompt, build_summary_prompt
from app.services.llm_service import get_llm_reply, get_structured_llm_reply
from app.session.manager import SessionManager
from app.session.store import get_or_create_session
from app.utils.observability import (
    build_observability_event,
    estimate_cost,
    write_jsonl,
)

_ERROR_TYPES_TO_CATCH = (RateLimitError, APITimeoutError, APIConnectionError, APIStatusError, ValueError)


def _classify_error(exc: Exception) -> tuple[str, int]:
    if isinstance(exc, RateLimitError):
        return "rate_limit", 429
    if isinstance(exc, APITimeoutError):
        return "timeout", 504
    if isinstance(exc, APIConnectionError):
        return "connection_error", 503
    if isinstance(exc, APIStatusError):
        return "provider_error", 502
    return "invalid_structured_output", 502


def _log_error(case_id: str, request: EventRequest, session: SessionManager, exc: Exception, prompt: str) -> None:
    error_type, status_code = _classify_error(exc)
    obs_event = build_observability_event(
        case_id=case_id,
        event_type=request.event_type,
        message=request.message,
        operation="no_state_update",
        state=session.state.model_dump(mode="json"),
        model=config.LLM_MODEL,
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        status="error",
        error_type=f"{status_code}_{error_type}",
        config=config.APP_CONFIG,
        prompt=prompt,
    )
    session.add_trace_event(obs_event)
    write_jsonl(config.APP_CONFIG["observability"]["request_log_path"], obs_event)


def process_event(case_id: str, request: EventRequest) -> EventResponse:
    session = get_or_create_session(case_id)
    prompt = build_context_prompt(session=session, user_message=request.message, config=config.APP_CONFIG)

    try:
        result = get_structured_llm_reply(
            prompt=prompt,
            model=config.LLM_MODEL,
            schema=ConversationUpdate,
            temperature=config.APP_CONFIG["llm"]["temperature"],
            max_tokens=config.APP_CONFIG["llm"]["max_tokens"],
            tool_name="update_conversation_state",
            tool_description="Update the case state and produce the next assistant message.",
            session_state=session.state,
            message=request.message,
        )
    except _ERROR_TYPES_TO_CATCH as exc:
        _log_error(case_id, request, session, exc, prompt)
        raise

    update = result.object
    merged_state = merge_state(existing=session.state, proposed=update.updated_state)
    state = apply_business_rules(merged_state)
    operation = determine_next_operation(state)

    session.add_message("user", request.message)
    session.update_state(state)
    session.add_message("assistant", update.assistant_message)

    summarized = False
    if not config.USE_MOCK_LLM and session.should_summarize(config.APP_CONFIG["context"]["summarize_after_messages"]):
        keep_last = config.APP_CONFIG["context"]["keep_last_messages_after_summary"]
        old_messages = session.messages[:-keep_last]
        summary_prompt = build_summary_prompt(existing_summary=session.summary, messages_to_summarize=old_messages)
        try:
            summary_result = get_llm_reply(prompt=summary_prompt, model=config.LLM_MODEL, temperature=0.0, max_tokens=250)
        except _ERROR_TYPES_TO_CATCH as exc:
            _log_error(case_id, request, session, exc, summary_prompt)
            raise
        session.compress_history(summary=summary_result.text, keep_last_messages=keep_last)
        summarized = True

    cost = estimate_cost(input_tokens=result.input_tokens, output_tokens=result.output_tokens, config=config.APP_CONFIG)
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
        config=config.APP_CONFIG,
        prompt=prompt,
    )
    session.add_trace_event(obs_event)
    write_jsonl(config.APP_CONFIG["observability"]["request_log_path"], obs_event)

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
            currency=config.APP_CONFIG["cost"]["currency"],
        ),
        prompt_version=config.APP_CONFIG["versions"]["prompt_version"],
        schema_version=config.APP_CONFIG["versions"]["schema_version"],
        rules_version=config.APP_CONFIG["versions"]["rules_version"],
    )
