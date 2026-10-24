import json
import os
from pathlib import Path

import pandas as pd
import yaml
from anthropic import Anthropic
from business_rules import apply_business_rules, determine_next_operation
from dotenv import load_dotenv
from llm_client import call_llm, call_llm_with_schema
from prompts import build_context_prompt, build_summary_prompt
from schemas import ConversationUpdate
from session_manager import SessionManager

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

load_dotenv()

client = Anthropic(
    api_key=os.getenv("LLM_API_KEY"),
    timeout=config["llm"]["timeout_seconds"],
)

model = config["llm"]["model"]
df = pd.read_csv(BASE_DIR / config["input_csv"])

sessions = {}
trace = []

for _, row in df.iterrows():
    session_id = row["session_id"]
    user_message = row["user_message"]

    if session_id not in sessions:
        sessions[session_id] = SessionManager(session_id)

    session = sessions[session_id]

    print(f'Processing {session_id} · turn {row["turn"]}...')

    # ! Llamada al Cliente con el stado incluido en el PROMP
    # ! La mejor solucion según nuestro profesor
    prompt = build_context_prompt(session, user_message, config)

    result = call_llm_with_schema(
        client=client,
        prompt=prompt,
        model=model,
        schema=ConversationUpdate,
        temperature=config["llm"]["temperature"],
        max_tokens=config["llm"]["max_tokens"],
        tool_name="update_conversation_state",
        tool_description="Update the conversation state and produce the next assistant message.",
    )

    update = result.object
    updated_state = apply_business_rules(update.updated_state)
    operation = determine_next_operation(updated_state)

    session.add_message("user", user_message)
    session.update_state(updated_state)
    session.add_message("assistant", update.assistant_message)

    summarized = False

    # ! Se hace una nueva llamada si han pasado x mensajes para hacer un resumen
    # ! creo que lo hace a modo de Ejemplo 2
    if session.should_summarize(config["context"]["summarize_after_messages"]):
        keep_last = config["context"]["keep_last_messages_after_summary"]
        old_messages = session.messages[:-keep_last]

        summary_prompt = build_summary_prompt(session.summary, old_messages)
        summary_result = call_llm(
            client=client,
            prompt=summary_prompt,
            model=model,
            temperature=config["llm"]["temperature"],
            max_tokens=config["llm"]["max_tokens"],
        )

        session.compress_history(
            summary=summary_result.text,
            keep_last_messages=keep_last,
        )
        summarized = True

    # ! La traza es el historial de los LOGS de todas las sesiones
    trace.append({
        "session_id": session_id,
        "turn": int(row["turn"]),
        "user_message": user_message,
        "assistant_message": update.assistant_message,
        "operation": operation,
        "summarized_after_turn": summarized,
        "state": updated_state.model_dump(mode="json"),
        "summary": session.summary,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    })

json_path = BASE_DIR / config["outputs"]["trace_json"]
csv_path = BASE_DIR / config["outputs"]["trace_csv"]

json_path.parent.mkdir(parents=True, exist_ok=True)

with json_path.open("w", encoding="utf-8") as f:
    json.dump(trace, f, indent=2, ensure_ascii=False)

# ! Una vez procesado TODO el CSV crea un dic para añadir la informacion a mostrar
# ! En la vida real no hariamos esto
flat_rows = []
for item in trace:
    state = item["state"]
    flat_rows.append({
        "session_id": item["session_id"],
        "turn": item["turn"],
        "user_message": item["user_message"],
        "assistant_message": item["assistant_message"],
        "operation": item["operation"],
        "process_type": state.get("process_type"),
        "priority": state.get("priority"),
        "order_id": state.get("order_id"),
        "reason": state.get("reason"),
        "delivery_address": state.get("delivery_address"),
        "missing_fields": "; ".join(state.get("missing_fields", [])),
        "requires_human_review": state.get("requires_human_review"),
        "ready_for_next_step": state.get("ready_for_next_step"),
        "summarized_after_turn": item["summarized_after_turn"],
        "latency_ms": item["latency_ms"],
        "input_tokens": item["input_tokens"],
        "output_tokens": item["output_tokens"],
    })

pd.DataFrame(flat_rows).to_csv(csv_path, index=False, encoding="utf-8")

print(f"Trace JSON saved to: {json_path}")
print(f"Trace CSV saved to: {csv_path}")
