"""Persistencia de conversaciones en el workspace del usuario."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..settings import CONVERSATIONS_DIR, WORK_DIR


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _jsonable(model_dump(mode="json", exclude_none=True))
    return value


class ConversationStore:
    """Guarda una transcripción visible y el historial de entrada de Responses API."""

    def __init__(self, directory: Path = CONVERSATIONS_DIR) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self._record_workspace()

    def _record_workspace(self) -> None:
        metadata_path = self.directory.parent / "workspace.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        metadata.setdefault("schema_version", 1)
        metadata.setdefault("created_at", _now())
        metadata["workspace"] = str(WORK_DIR)
        metadata["last_opened_at"] = _now()
        temporary_path = metadata_path.with_name(f"workspace.{uuid.uuid4().hex}.tmp")
        temporary_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary_path, metadata_path)

    def create(self) -> dict[str, Any]:
        now = _now()
        conversation = {
            "id": uuid.uuid4().hex,
            "title": "Nueva conversación",
            "created_at": now,
            "updated_at": now,
            "events": [],
            "agent_history": [],
            "run_count": 0,
        }
        self._save(conversation)
        return conversation

    def get(self, conversation_id: str) -> dict[str, Any] | None:
        try:
            normalized = uuid.UUID(hex=conversation_id).hex
        except (ValueError, AttributeError):
            return None
        path = self.directory / f"{normalized}.json"
        try:
            conversation = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return conversation if isinstance(conversation, dict) else None

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        conversations: list[dict[str, Any]] = []
        for path in self.directory.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                conversations.append(item)
        conversations.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return conversations[:limit]

    def latest(self) -> dict[str, Any] | None:
        items = self.list(limit=1)
        return items[0] if items else None

    def add_event(
        self,
        conversation_id: str,
        speaker: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        conversation = self.get(conversation_id)
        if conversation is None:
            return
        conversation.setdefault("events", []).append(
            {
                "time": _now(),
                "speaker": speaker,
                "message": message,
                "details": _jsonable(details or {}),
            }
        )
        if speaker == "Tú" and conversation.get("title") == "Nueva conversación":
            title = " ".join(message.split())
            conversation["title"] = title[:72] + ("…" if len(title) > 72 else "")
        conversation["updated_at"] = _now()
        self._save(conversation)

    def save_agent_state(
        self,
        conversation_id: str,
        history: list[Any],
        run_count: int,
    ) -> None:
        conversation = self.get(conversation_id)
        if conversation is None:
            return
        conversation["agent_history"] = _jsonable(history)
        conversation["run_count"] = run_count
        conversation["updated_at"] = _now()
        self._save(conversation)

    def _save(self, conversation: dict[str, Any]) -> None:
        path = self.directory / f"{conversation['id']}.json"
        temporary_path = path.with_name(f"{path.stem}.{uuid.uuid4().hex}.tmp")
        temporary_path.write_text(
            json.dumps(_jsonable(conversation), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary_path, path)
