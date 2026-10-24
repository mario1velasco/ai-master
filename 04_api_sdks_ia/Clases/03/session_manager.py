from schemas import ConversationState


class SessionManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = []
        self.summary = ""
        self.state = ConversationState()

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
