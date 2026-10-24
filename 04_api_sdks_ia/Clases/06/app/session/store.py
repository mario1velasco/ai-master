from app.session.manager import SessionManager

_SESSIONS: dict[str, SessionManager] = {}

def get_or_create_session(case_id: str) -> SessionManager:
    if case_id not in _SESSIONS:
        _SESSIONS[case_id] = SessionManager(case_id=case_id)
    return _SESSIONS[case_id]

def get_session(case_id: str) -> SessionManager | None:
    return _SESSIONS.get(case_id)

def delete_session(case_id: str) -> bool:
    return _SESSIONS.pop(case_id, None) is not None

def list_case_ids() -> list[str]:
    return sorted(_SESSIONS.keys())

def clear_sessions() -> None:
    _SESSIONS.clear()
