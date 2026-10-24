"""Level 3. Same business prompt as Level 2, but the structured-output
mechanism is a forced tool call instead of `output_config.format`.

No usamos agentes ni un bucle de tool-execution: `tool_choice` fuerza a
Claude a llamar SIEMPRE a `extract_ticket_analysis`; la tool definition
(TICKET_ANALYSIS_TOOL, en schema_tool.py) hace de schema, y el `input` de
ese tool_use block es la salida estructurada.
"""

import json
import os
from pathlib import Path
from time import perf_counter

import pandas as pd
import yaml
from anthropic import Anthropic, APIError
from dotenv import load_dotenv
from prompts import build_business_prompt
from pydantic import ValidationError
from schema_tool import TICKET_ANALYSIS_TOOL, TicketAnalysisTool

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

load_dotenv()

api_key = os.getenv("LLM_API_KEY")
model = config["llm"]["model"]

if not api_key:
    raise ValueError("LLM_API_KEY is missing from .env")
if not model:
    raise ValueError("LLM_MODEL is missing from config.yml")

client = Anthropic(
    api_key=api_key,
    timeout=config["llm"]["timeout_seconds"],
)

df = pd.read_csv(BASE_DIR / config["input_csv"])
results = []

for _, row in df.iterrows():
    request_id = row["request_id"]
    print(f"Processing {request_id} with a forced tool call...")

    # ! Mismo prompt de negocio que Level 2: el schema no va en el texto,
    # ! va en la tool definition (TICKET_ANALYSIS_TOOL).
    prompt = build_business_prompt(row["customer_request"], config)
    result = None
    analysis = None
    tool_input = None
    start = perf_counter()

    try:
        # ! tool_choice fuerza a Claude a llamar SIEMPRE a esta tool concreta,
        # ! en vez de dejarle decidir (type: "auto") o exigir alguna (type: "any").
        result = client.messages.create(
            model=model,
            max_tokens=config["llm"]["max_tokens"],
            temperature=config["llm"]["temperature"],
            messages=[{"role": "user", "content": prompt}],
            tools=[TICKET_ANALYSIS_TOOL],
            tool_choice={"type": "tool", "name": TICKET_ANALYSIS_TOOL["name"]},
        )

        if result.stop_reason == "refusal":
            raise ValueError("Claude refused the request.")
        if result.stop_reason == "max_tokens":
            raise ValueError(
                "The tool call was truncated. Increase max_tokens."
            )

        # ! Buscamos el tool_use block (puede haber bloques de texto antes)
        for block in result.content:
            if block.type == "tool_use" and block.name == TICKET_ANALYSIS_TOOL["name"]:
                tool_input = block.input
                break
        
        if tool_input is None:
            raise ValueError("Claude did not call the expected tool.")


        # ! El input ya llega parseado como dict: lo validamos con Pydantic
        analysis = TicketAnalysisTool.model_validate(tool_input)
        status = "valid"
        error = ""

    except ValidationError as exc:
        status = "validation_error"
        error = str(exc)

    except (APIError, ValueError) as exc:
        status = "error"
        error = str(exc)

    latency_ms = int((perf_counter() - start) * 1000)

    results.append(
        {
            "request_id": request_id,
            "status": status,
            "process_type": analysis.process_type.value if analysis else "",
            "priority": analysis.priority.value if analysis else "",
            "order_id": analysis.order_id if analysis else "",
            "reason": analysis.reason if analysis else "",
            "requires_human_review": (
                analysis.requires_human_review if analysis else ""
            ),
            "suggested_action": analysis.suggested_action if analysis else "",
            "expected_process_type": row.get("expected_process_type", ""),
            "expected_priority": row.get("expected_priority", ""),
            "expected_order_id": row.get("expected_order_id", ""),
            "model": model,
            "latency_ms": latency_ms,
            "input_tokens": result.usage.input_tokens if result else "",
            "output_tokens": result.usage.output_tokens if result else "",
            "error": error,
            "raw_tool_input": 
                json.dumps(tool_input, ensure_ascii=False)
                if tool_input else "",
        }
    )

output_path = BASE_DIR / config["outputs"]["tool_call_csv"]
output_path.parent.mkdir(parents=True, exist_ok=True)

pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8")

print(f"Structured extraction with forced tool call (Level 3) completed: {output_path}")
