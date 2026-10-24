"""Level 1: request JSON in the prompt, then parse and validate it."""

import json
import os
from pathlib import Path

import pandas as pd
import yaml
from anthropic import Anthropic, APIError
from dotenv import load_dotenv
from pydantic import ValidationError

from llm_client import call_llm
from prompts import build_prompt_json_prompt
from schemas import TicketAnalysis

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
    print(f"Processing {request_id} with prompt-only JSON...")

    # ! Creamos el prompt a partir de prompts.py de la fila del CSV
    prompt = build_prompt_json_prompt(row["customer_request"], config)
    result = None
    analysis = None

    try:
        # ! USAMOS call_llm
        result = call_llm(
            client=client,
            prompt=prompt,
            model=model,
            temperature=config["llm"]["temperature"],
            max_tokens=config["llm"]["max_tokens"],
        )

        # ! Parseamos como JSON. Va a fallar muchisimas veces (except invalid_json)
        data = json.loads(result.text)
        # ! Encapsular como objeto de TicketAnalisis. Va a fallar muchisimas veces (except validation_error)
        analysis = TicketAnalysis.model_validate(data)
        status = "valid"
        error = ""

    except json.JSONDecodeError as exc:
        status = "invalid_json"
        error = str(exc)

    except ValidationError as exc:
        status = "validation_error"
        error = str(exc)

    except (APIError, ValueError) as exc:
        status = "api_error"
        error = str(exc)

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
            "latency_ms": result.latency_ms if result else "",
            "input_tokens": result.input_tokens if result else "",
            "output_tokens": result.output_tokens if result else "",
            "input_chars": result.input_chars if result else len(prompt),
            "output_chars": result.output_chars if result else "",
            "error": error,
            "raw_output": result.text if result else "",
        }
    )

output_path = BASE_DIR / config["outputs"]["prompt_json_csv"]
output_path.parent.mkdir(parents=True, exist_ok=True)

pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8")

print(f"Structured extraction (Level 1) completed: {output_path}")
