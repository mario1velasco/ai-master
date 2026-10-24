from app.domain.schemas import ConversationState, Priority, ProcessType

REQUIRED_FIELDS = {
    ProcessType.refund_request: ["order_id", "reason"], 
    ProcessType.delivery_change: ["order_id", "delivery_address"],
    ProcessType.delivery_delay: ["order_id"],
    ProcessType.billing_issue: ["order_id", "reason"],
    ProcessType.technical_support: ["reason"],
    ProcessType.account_management: ["reason"],
    ProcessType.other: [],
}

def merge_state(existing: ConversationState, proposed: ConversationState) -> ConversationState:
    """Preserve known state unless the proposed update contains a non-empty value."""
    data = existing.model_dump()
    for field_name, value in proposed.model_dump().items():
        if field_name in {"missing_fields", "ready_for_next_step", "requires_human_review"}:
            continue
        if value not in (None, "", []):
            data[field_name] = value
    if proposed.requires_human_review:
        data["requires_human_review"] = True
    return ConversationState(**data)

def apply_business_rules(state: ConversationState) -> ConversationState:
    if state.process_type is None:
        state.missing_fields = ["process_type"]
        state.ready_for_next_step = False
        return state
    required = REQUIRED_FIELDS.get(state.process_type, [])
    missing = [field for field in required if getattr(state, field) in (None, "", [])]
    if state.priority == Priority.high:
        state.requires_human_review = True
    state.missing_fields = missing
    state.ready_for_next_step = len(missing) == 0 and not state.requires_human_review
    return state

def determine_next_operation(state: ConversationState) -> str:
    if state.requires_human_review:
        return "send_to_human_review"
    if state.missing_fields:
        return f"ask_for_{state.missing_fields[0]}"
    if not state.ready_for_next_step:
        return "continue_conversation"
    if state.process_type == ProcessType.refund_request:
        return "start_refund_validation"
    if state.process_type == ProcessType.delivery_change:
        return "start_delivery_change_workflow"
    if state.process_type == ProcessType.delivery_delay:
        return "check_delivery_status"
    if state.process_type == ProcessType.billing_issue:
        return "open_billing_review"
    if state.process_type == ProcessType.technical_support:
        return "open_technical_ticket"
    return "route_to_general_queue"
