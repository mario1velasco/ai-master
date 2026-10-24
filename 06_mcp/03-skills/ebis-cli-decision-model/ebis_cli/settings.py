"""Valores centrales del harness, visibles y fáciles de cambiar en clase."""

from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
WORK_DIR = Path.cwd().resolve()

# Número máximo de servidores stdio/HTTP que se conectan en un mismo arranque.
MAX_MCP_SERVERS = 10

MAX_AGENT_STEPS = 16
MAX_SUBAGENT_STEPS = 6
MAX_CONTEXT_BUILDS = 2
MAX_HISTORY_ITEMS = 80
MAX_COMMAND_SECONDS = 120
MAX_TOOL_OUTPUT_CHARS = 20_000
MAX_SUBAGENT_RESULT_CHARS = 12_000
WORKSPACE_TIMEZONE = "Europe/Madrid"
DECISION_MODEL_ENABLED_DEFAULT = True

# Tarifa pública de Jev/TypeSafe usada para estimar el coste en /stats.
# Configurable para reflejar cambios de precio o acuerdos de cuenta distintos.
JEV_INPUT_USD_PER_MILLION = 0.042
JEV_OUTPUT_USD_PER_MILLION = 0.0

EBIS_HOME = WORK_DIR / ".ebis_cli"
CONVERSATIONS_DIR = EBIS_HOME / "conversations"
USAGE_FILE = EBIS_HOME / "usage.json"
ROUTING_FILE = CODE_DIR / "routing-llm.json"
