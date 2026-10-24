import json
from textwrap import dedent

from schemas import TicketAnalysis




# * ****** LEVEL 1 BASELINE: thr JSON schema is embedded in the prompt text ******
def build_prompt_json_prompt(customer_request: str, config: dict) -> str:
    """Level 1 baseline: the JSON schema is embedded in the prompt text."""

    # ! Sacamos el schema de la clase TicketAnalysis (schemas.py)
    schema = json.dumps(
        TicketAnalysis.model_json_schema(),
        indent=2,
        ensure_ascii=False,
    )

    # ! esto esta mal hecho JSON schema:
    # !{schema}
    # !  Mirar Level 2

    return dedent(
        f"""
        {config["prompt"]["role"]}

        Task:
        {config["prompt"]["task_json"]}

        Customer request:
        <request>
        {customer_request}
        </request>

        Business rules:
        {config["prompt"]["instructions"]}

        JSON schema:
        {schema}

        Output rules:
        {config["prompt"]["output_format"]}
        """
    ).strip()

# * ****** LEVEL 2: we dont have the JSON schema ******
def build_business_prompt(customer_request: str, config: dict) -> str:
    """Level 2: Prompt usaewd with nativer Structured Outputs and tool calls.

    The prompt explain the bussines task. The technical output schema is passed
    separately through the Antropic API.
    
    """

    return dedent(
        f"""
        {config["prompt"]["role"]}

        Task:
        {config["prompt"]["task_bussines"]}

        Customer request:
        <request>
        {customer_request}
        </request>

        Business rules:
        {config["prompt"]["instructions"]}

        Keep suggested_action short and operational.
        """
    ).strip()