"""Level 2: Anthreopic native Structured Outputs with Pydantic schema.
Antropic API call with nativer Structured Outputs and tool calls.

The prompt explain the bussines task. The technical output schema is passed
separately through the Antropic API.

"""

import os
from pathlib import Path
from time import perf_counter

import pandas as pd
import yaml
from anthropic import Anthropic, APIError
from dotenv import load_dotenv
from prompts import build_business_prompt
from pydantic import ValidationError
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
    print(f"Processing {request_id} with Anthropic Structured Outputs...")

    # ! Creamos el prompt a partir de prompts.py de la fila del CSV
    prompt = build_business_prompt(row["customer_request"], config)
    result = None
    analysis = None
    raw_output = ""
    start = perf_counter()

    try:
        # ! USAMOS LA API DE ANTHROPIC
        result = client.messages.parse(
            model=model,
            max_tokens=config["llm"]["max_tokens"],
            temperature=config["llm"]["temperature"],
            messages=[{"role": "user", "content": prompt}],
            # ! Pasamos el schema de la clase TicketAnalysis (schemas.py)
            output_format=TicketAnalysis,
        )

        print(result)

        raw_output = "\n".join(
            block.text
            for block in result.content
            if block.type == "text"
        ).strip()

        if result.stop_reason == "refusal":
            raise ValueError("Claude refused the request.")
        if result.stop_reason == "max_tokens":
            raise ValueError(
                "The structured response was truncated. Increase max_tokens."
            )
        if result.parsed_output is None:
            raise ValueError("Anthropic returned no parsed structured output.")

        analysis = result.parsed_output
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
            "raw_output": raw_output,
        }
    )

output_path = BASE_DIR / config["outputs"]["structured_output_csv"]
output_path.parent.mkdir(parents=True, exist_ok=True)

pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8")

print(f"Structured extraction (Level 2) completed: {output_path}")
