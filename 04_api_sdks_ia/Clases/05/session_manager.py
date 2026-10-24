from datetime import datetime, timezone
from typing import Any
from schemas import ConversationState

class SessionManager:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.messages: list[dict[str, str]] = []
        self.summary: str = ""
        self.state = ConversationState()
        self.trace: list[dict[str, Any]] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self._touch()

    def recent_messages(self, max_messages: int) -> list[dict[str, str]]:
        return self.messages[-max_messages:]

    def update_state(self, new_state: ConversationState) -> None:
        self.state = new_state
        self._touch()

    def should_summarize(self, threshold: int) -> bool:
        return len(self.messages) > threshold

    def compress_history(self, summary: str, keep_last_messages: int) -> None:
        self.summary = summary
        self.messages = self.messages[-keep_last_messages:]
        self._touch()

    def add_trace_event(self, event: dict[str, Any]) -> None:
        self.trace.append(event)
        self._touch()

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "state": self.state.model_dump(mode="json"),
            "summary": self.summary,
            "messages": self.messages,
            "trace_size": len(self.trace),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
