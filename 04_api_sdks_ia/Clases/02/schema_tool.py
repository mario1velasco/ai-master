"""Level 3 schema: real tool calls as the structured-output mechanism.

No usamos agentes ni un bucle de tool-execution: `TICKET_ANALYSIS_TOOL` es la
tool definition que forzamos con `tool_choice` (ver structured_extract_3_tool.py),
y `TicketAnalysisTool` valida el `input` de ese tool_use block.
"""

from enum import Enum
from typing import Optional

from anthropic.types import ToolParam
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


TICKET_ANALYSIS_TOOL: ToolParam = {
    "name": "extract_ticket_analysis",
    "description": (
        "Extract the structured customer-service analysis required by the "
        "downstream workflow. Use only information explicitly present in the "
        "customer request. Return null for absent optional values and mark "
        "requires_human_review as true when the request is ambiguous, "
        "incomplete, high-risk or cannot be safely automated."
    ),
    # ! strict = true. Enfatizamos que los argumentos al schema son estrictos
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "process_type": {
                "type": "string",
                "enum": [item.value for item in ProcessType]
            },
            "priority": {
                "type": "string",
                "enum": [item.value for item in Priority]
            },
            "order_id": {"type": ["string", "null"]},
            "reason": {"type": ["string", "null"]},
            "requires_human_review": {"type": "boolean"},
            "suggested_action": {"type": "string"}
        },
        "required": ["process_type", "priority", "order_id", "reason",
                    "requires_human_review", "suggested_action"],
        # ! additionalProperties = false. No aceptamos argumentos adicionales
        "additionalProperties": False,
    }
}


class TicketAnalysisTool(BaseModel):
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
