from app.domain.business_rules import (
    apply_business_rules,
    determine_next_operation,
    merge_state,
)
from app.domain.schemas import ConversationState, Priority, ProcessType


def test_refund_request_missing_order_id(): 
    state = ConversationState(process_type=ProcessType.refund_request, reason="damaged_item", priority=Priority.medium)
    state = apply_business_rules(state)
    assert state.ready_for_next_step is False
    assert state.missing_fields == ["order_id"]
    assert determine_next_operation(state) == "ask_for_order_id"

def test_high_priority_goes_to_human_review():
    state = ConversationState(process_type=ProcessType.billing_issue, order_id="9901", reason="charged_twice", priority=Priority.high)
    state = apply_business_rules(state)
    assert state.requires_human_review is True
    assert state.ready_for_next_step is False
    assert determine_next_operation(state) == "send_to_human_review"

def test_merge_state_preserves_existing_order_id():
    existing = ConversationState(process_type=ProcessType.refund_request, order_id="8921", reason="damaged_item", priority=Priority.medium)
    proposed = ConversationState(process_type=ProcessType.refund_request, order_id=None, reason=None, priority=Priority.medium)
    merged = merge_state(existing, proposed)
    assert merged.order_id == "8921"
    assert merged.reason == "damaged_item"
