from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProcessType(str, Enum):
    refund_request = "refund_request"
    delivery_change = "delivery_change"
    delivery_delay = "delivery_delay"
    technical_support = "technical_support"
    billing_issue = "billing_issue"
    product_question = "product_question"
    account_management = "account_management"
    other = "other"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TicketAnalysis(BaseModel):
    """Validated business object returned by the LLM."""

    model_config = ConfigDict(extra="forbid")

    process_type: ProcessType = Field(
        description="Main customer-service workflow triggered by the request."
    )
    priority: Priority = Field(
        description="Operational priority used for queueing and SLA management."
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Order ID only when it is explicitly present in the request.",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Short normalized reason for the request, or null if unavailable.",
    )
    requires_human_review: bool = Field(
        description="True when the request is ambiguous, incomplete, high-risk or cannot be safely automated."
    )
    suggested_action: str = Field(
        min_length=3,
        max_length=180,
        description="Short operational next action for the downstream workflow.",
    )
