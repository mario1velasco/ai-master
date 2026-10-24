from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProcessType(str, Enum):
    refund_request = "refund_request"
    delivery_change = "delivery_change"
    delivery_delay = "delivery_delay"
    technical_support = "technical_support"
    billing_issue = "billing_issue"
    account_management = "account_management"
    other = "other"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ConversationState(BaseModel):
    process_type: Optional[ProcessType] = None
    priority: Optional[Priority] = None
    order_id: Optional[str] = None
    reason: Optional[str] = None
    delivery_address: Optional[str] = None
    requires_human_review: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    ready_for_next_step: bool = False

class ConversationUpdate(BaseModel):
    assistant_message: str = Field(max_length=500, description="Short operational message to send back to the user.")
    updated_state: ConversationState
