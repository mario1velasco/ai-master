from schemas import ConversationState


class SessionManager:
    """In-memory conversation state and trace for a single case."""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.messages: list[dict] = []
        self.summary = ""
        self.state = ConversationState()
        self.trace: list = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def recent_messages(self, max_messages: int) -> list[dict]:
        return self.messages[-max_messages:]

    def update_state(self, new_state: ConversationState) -> None:
        self.state = new_state

    def should_summarize(self, threshold: int) -> bool:
        return len(self.messages) > threshold

    def compress_history(self, summary: str, keep_last_messages: int) -> None:
        self.summary = summary
        self.messages = self.messages[-keep_last_messages:]

    def add_trace_event(self, event) -> None:
        self.trace.append(event)

    def to_snapshot(self) -> dict:
        return {
            "summary": self.summary,
            "messages": self.messages,
            "trace_size": len(self.trace),
        }
