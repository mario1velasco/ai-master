import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ! IMP. Control de coste
def estimate_cost(input_tokens: int, output_tokens: int, config: dict) -> float:
    input_cost = input_tokens * config["cost"]["input_cost_per_1m_tokens"] / 1_000_000
    output_cost = output_tokens * config["cost"]["output_cost_per_1m_tokens"] / 1_000_000
    return round(input_cost + output_cost, 8)

# ! Importante para los LOGs
def build_observability_event(*, case_id: str, event_type: str, message: str, operation: str, state: dict, model: str, latency_ms: int, input_tokens: int, output_tokens: int, status: str, config: dict, error_type: str | None = None, prompt: str | None = None) -> dict[str, Any]:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "deployment_environment": config["app"]["deployment_environment"],
        "case_id": case_id,
        "event_type": event_type,
        "message_chars": len(message),
        "operation": operation,
        "status": status,
        "error_type": error_type,
        "model": model,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimate_cost(input_tokens, output_tokens, config),
        "currency": config["cost"]["currency"],
        "prompt_version": config["versions"]["prompt_version"],
        "schema_version": config["versions"]["schema_version"],
        "rules_version": config["versions"]["rules_version"],
        "state": state,
    }
    if config["observability"].get("include_prompt_preview") and prompt:
        chars = config["observability"].get("prompt_preview_chars", 400)
        event["prompt_preview"] = prompt[:chars]
    return event


def write_jsonl(path: str, event: dict[str, Any]) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> list[dict[str, Any]]:
    log_path = Path(path)
    if not log_path.exists():
        return []
    with log_path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
