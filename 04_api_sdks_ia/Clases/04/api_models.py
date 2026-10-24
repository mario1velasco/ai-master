from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas import ConversationState


class EventRequest(BaseModel):
    event_type: Literal[
        "user_message",
        "email_received",
        "operator_comment",
        "manual_update",
    ] = "user_message"
    message: str = Field(min_length=1, max_length=3000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    case_id: str
    event_type: str
    assistant_message: str
    operation: str
    state: ConversationState
    summarized: bool
    latency_ms: int
    input_tokens: int
    output_tokens: int
    model: str


class CaseStateResponse(BaseModel):
    case_id: str
    state: ConversationState
    summary: str
    messages: list[dict[str, str]]
    trace_size: int


class TraceResponse(BaseModel):
    case_id: str
    trace: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    model_configured: bool
    api_key_configured: bool
