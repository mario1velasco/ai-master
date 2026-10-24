# main.py
import os

import yaml
from anthropic import Anthropic
from dotenv import load_dotenv

from llm_client import call_llm

with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

load_dotenv()

client = Anthropic(
    api_key=os.getenv("LLM_API_KEY"),
    timeout=config["llm"]["timeout_seconds"],
)
model = config["llm"]["model"]

prompt =  """
Summarize the following customer request: "
My order arrived damaged and I need a replacement as soon as possible.

Return:
- Summary
- Category
- Priority
- Suggested next action
"""

result = call_llm(client, prompt, model=model)

print('--------------RESULT -------------------')
print(result)
print('--------------Response-------------------')
print(result.text)
print('--------------Latency-------------------')
print(result.latency_ms)
