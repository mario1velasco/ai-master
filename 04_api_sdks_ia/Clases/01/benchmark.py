# benchmark.py
import os
from pathlib import Path

import pandas as pd
import yaml
from anthropic import Anthropic
from dotenv import load_dotenv

from llm_client import call_llm

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

results = []

for _, row in df.iterrows():
    prompt = f"""
                {config["prompt"]["role"]}

                Task:
                {row["task"]}

                Customer request:
                {row["customer_request"]}

                Instructions:
                {config["prompt"]["instructions"]}

                Output format:
                {config["prompt"]["output_format"]}
            """

    print(f'Processing {row["request_id"]}...')

    try:
        result = call_llm(
            client=client,
            prompt=prompt,
            model=model,
            temperature=config["llm"]["temperature"],  
            max_tokens=config["llm"]["max_tokens"],  
        )

        print()

        results.append({
            "request_id": row["request_id"],
            "task": row["task"],
            "customer_request": row["customer_request"],
            "expected_category": row["expected_category"],
            "expected_priority": row["expected_priority"],
            "model": result.model,
            "temperature": config["llm"]["temperature"],
            "max_tokens": config["llm"]["max_tokens"],
            "latency_ms": result.latency_ms,
            "input_tokens": result.input_tokens,  
            "output_tokens": result.output_tokens, 
            "input_chars": result.input_chars,
            "output_chars": result.output_chars,
            "status": "ok",
            "output": result.text,  
        })
    except Exception as e:
        print(f"Error: {e}")
        print()

        results.append({
            "request_id": row["request_id"],
            "task": row["task"],
            "customer_request": row["customer_request"],
            "expected_category": row["expected_category"],
            "expected_priority": row["expected_priority"],
            "model": model,
            "temperature": config["llm"]["temperature"],
            "max_tokens": config["llm"]["max_tokens"],
            "latency_ms": None,
            "input_tokens": None, 
            "output_tokens": None, 
            "input_chars": len(prompt),
            "output_chars": None,
            "status": "error",
            "output": str(e),  
        })

output_path = BASE_DIR / config["output_csv"]
output_path.parent.mkdir(parents=True, exist_ok=True)

pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8")

print(f"Benchmark completed: {output_path}")
