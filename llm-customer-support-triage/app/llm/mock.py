import re
from time import perf_counter

from app.api_clients.anthropic_client import StructuredLLMResult
from app.domain.business_rules import apply_business_rules
from app.domain.schemas import ConversationState, ConversationUpdate, Priority, ProcessType


def mock_call_llm_with_schema(session_state: ConversationState, message: str) -> StructuredLLMResult:
    """Deterministic local substitute for CI, tests and classroom demos."""
    start = perf_counter()
    state = ConversationState(**session_state.model_dump())
    text = message.lower()

    if any(word in text for word in ["return", "refund", "cancel"]):
        state.process_type = ProcessType.refund_request

    if "delivery" in text and any(word in text for word in ["change", "address"]):
        state.process_type = ProcessType.delivery_change

    if any(word in text for word in ["delay", "late", "where is my order"]):
        state.process_type = ProcessType.delivery_delay

    if any(word in text for word in ["charged", "billing", "invoice", "payment"]):
        state.process_type = ProcessType.billing_issue

    if any(word in text for word in ["login", "token", "platform", "access"]):
        state.process_type = ProcessType.technical_support

    order_match = re.search(r"\b(\d{4,})\b", message)
    if order_match:
        state.order_id = order_match.group(1)

    if any(word in text for word in ["broken", "damaged", "charged twice", "invalid token", "cannot access"]):
        if "charged" in text:
            state.reason = "charged_twice"
        elif "token" in text or "access" in text:
            state.reason = "access_error"
        else:
            state.reason = "damaged_item"

    if "new address is" in text:
        state.delivery_address = message.lower().split("new address is", 1)[-1].strip().strip(".").title()

    if any(word in text for word in ["urgent", "third time", "charged twice"]):
        state.priority = Priority.high
    elif state.priority is None:
        state.priority = Priority.medium

    preview_state = apply_business_rules(ConversationState(**state.model_dump()))
    if preview_state.requires_human_review:
        assistant = "I will route this case to a human reviewer."
    elif preview_state.missing_fields:
        assistant = f"Could you provide the {preview_state.missing_fields[0]}?"
    else:
        assistant = "Thanks. I have enough information to continue the workflow."

    update = ConversationUpdate(assistant_message=assistant, updated_state=state)
    latency_ms = int((perf_counter() - start) * 1000)

    return StructuredLLMResult(
        object=update,
        raw_tool_input=update.model_dump(mode="json"),
        model="mock-triage-model",
        latency_ms=latency_ms,
        input_tokens=max(1, len(message) // 4),
        output_tokens=50,
    )
