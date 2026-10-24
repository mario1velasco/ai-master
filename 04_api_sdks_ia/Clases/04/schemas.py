"""Level 3 schema: real tool calls as the structured-output mechanism.

No usamos agentes ni un bucle de tool-execution: `CONVERSATION_UPDATE_TOOL` es la
tool definition que forzamos con `tool_choice` (ver structured_extract_3_tool.py),
y `ConversationUpdate` valida el `input` de ese tool_use block.
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


CONVERSATION_UPDATE_TOOL: ToolParam = {
    "name": "update_conversation_state",
    "description": (
        "Update the tracked conversation state with any new information "
        "explicitly present in the latest customer message, and produce the "
        "next assistant reply. Keep fields already known unless the customer "
        "contradicts them. List in missing_fields any of process_type, "
        "priority or order_id that are still unknown, and set "
        "ready_for_next_step to true only when nothing is missing."
    ),
    # ! strict = true. Enfatizamos que los argumentos al schema son estrictos
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "assistant_message": {"type": "string", "maxLength": 500},
            "updated_state": {
                "type": "object",
                "properties": {
                    "process_type": {
                        "type": ["string", "null"],
                        "enum": [item.value for item in ProcessType] + [None]
                    },
                    "priority": {
                        "type": ["string", "null"],
                        "enum": [item.value for item in Priority] + [None]
                    },
                    "order_id": {"type": ["string", "null"]},
                    "reason": {"type": ["string", "null"]},
                    "missing_fields": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "ready_for_next_step": {"type": "boolean"},
                },
                "required": ["process_type", "priority", "order_id", "reason",
                            "missing_fields", "ready_for_next_step"],
                # ! additionalProperties = false también en el objeto anidado
                "additionalProperties": False,
            },
        },
        "required": ["assistant_message", "updated_state"],
        # ! additionalProperties = false. No aceptamos argumentos adicionales
        "additionalProperties": False,
    }
}


class ConversationState(BaseModel):
    """Business fields accumulated across the conversation so far."""

    model_config = ConfigDict(extra="forbid")

    process_type: Optional[ProcessType] = Field(
        default=None, 
        description="Main customer-service workflow triggered by the request, once known.",
    )
    priority: Optional[Priority] = Field(
        default=None,
        description="Operational priority used for queueing and SLA management, once known.",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Order ID only when it is explicitly present in the conversation.",
    )
    delivery_address: Optional[str] = Field(
        default=None,
        description="New delivery address, only for delivery_change requests.",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Short normalized reason for the request, or null if unavailable.",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Names of business fields still needed before the ticket can be routed.",
    )
    ready_for_next_step: bool = Field(
        default=False,
        description="True once all required fields are known and the ticket can move forward.",
    )
    requires_human_review: bool = Field(
        default=False,
        description="True when a business rule requires escalating the ticket to a human.",
    )


class ConversationUpdate(BaseModel):
    """Validated business object returned by the LLM."""

    model_config = ConfigDict(extra="forbid")

    assistant_message: str = Field(
        max_length=500,
        description="Next reply shown to the customer.",
    )
    updated_state: ConversationState
