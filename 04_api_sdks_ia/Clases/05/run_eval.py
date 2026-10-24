import argparse
import json
import os
from pathlib import Path

import pandas as pd
import yaml
from business_rules import apply_business_rules, determine_next_operation, merge_state
from dotenv import load_dotenv
from llm_client import call_llm_with_schema
from mock_llm import mock_call_llm_with_schema
from prompts import build_context_prompt
from schemas import ConversationUpdate
from session_manager import SessionManager


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def compare_expected(final_state: dict, operation: str, expected: dict) -> tuple[bool, list[str]]:
    errors = []
    for key, expected_value in expected.items():
        actual_value = operation if key == "operation" else final_state.get(key)
        if actual_value != expected_value:
            errors.append(f"{key}: expected={expected_value!r}, actual={actual_value!r}")
    return len(errors) == 0, errors

def run_case(case: dict, config: dict, mode: str, client=None, model: str | None = None) -> dict:
    session = SessionManager(case_id=case["case_id"])
    last_operation = "not_started"
    for message in case["events"]:
        prompt = build_context_prompt(session=session, user_message=message, config=config)
        if mode == "mock":
            result = mock_call_llm_with_schema(session_state=session.state, message=message)
        else:
            if model is None:
                raise RuntimeError("LLM_MODEL is required in real mode.")
            result = call_llm_with_schema(client=client, prompt=prompt, model=model, schema=ConversationUpdate, temperature=config["llm"]["temperature"], max_tokens=config["llm"]["max_tokens"], tool_name="update_conversation_state", tool_description="Update the case state and produce the next assistant message.")
        update = result.object
        merged_state = merge_state(session.state, update.updated_state)
        state = apply_business_rules(merged_state)
        last_operation = determine_next_operation(state)
        session.add_message("user", message)
        session.update_state(state)
        session.add_message("assistant", update.assistant_message)
    final_state = session.state.model_dump(mode="json")
    passed, errors = compare_expected(final_state, last_operation, case["expected"])
    return {"case_id": case["case_id"], "description": case["description"], "passed": passed, "errors": errors, "operation": last_operation, "final_state": final_state, "expected": case["expected"]}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--cases", default="eval_cases.yml")
    args = parser.parse_args()
    config = load_yaml(args.config)
    eval_data = load_yaml(args.cases)
    client = None
    model = None
    if args.mode == "real":
        load_dotenv()
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL")
        if not api_key or not model:
            raise RuntimeError("LLM_API_KEY and LLM_MODEL are required in real mode.")
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key, timeout=int(os.getenv("LLM_TIMEOUT_SECONDS", "30")))
    results = [run_case(case, config=config, mode=args.mode, client=client, model=model) for case in eval_data["cases"]]
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    summary = {"mode": args.mode, "eval_set_version": config["versions"]["eval_set_version"], "total_cases": total, "passed": passed, "failed": total-passed, "pass_rate": round(passed/total if total else 0, 4)}
    outputs = Path("outputs")
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "eval_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (outputs / "eval_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame([{"case_id": r["case_id"], "description": r["description"], "passed": r["passed"], "operation": r["operation"], "errors": " | ".join(r["errors"])} for r in results]).to_csv(outputs / "eval_results.csv", index=False)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
