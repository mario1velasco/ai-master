#!/usr/bin/env bash
# Lanza JupyterLab con el .venv común de la raíz y el .env raíz exportado al proceso.
# Uso:  scripts/lab.sh [carpeta]     (por defecto, la raíz del repo)
# Los notebooks usan load_dotenv(override=False)/setdefault: respetan estas variables.
# El .env se interpreta con python-dotenv (no con el shell) y NO se imprime.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || { echo "Falta $ROOT/.venv (ver CLAUDE.md)." >&2; exit 1; }
if [ -f "$ROOT/.env" ]; then
  eval "$("$PY" - "$ROOT/.env" <<'PYEOF'
import shlex, sys
from dotenv import dotenv_values
for key, value in dotenv_values(sys.argv[1]).items():
    if value:
        print(f"export {key}={shlex.quote(value)}")
PYEOF
)"
fi
export PATH="$ROOT/.venv/bin:$PATH"
cd "${1:-$ROOT}"
exec python -m jupyterlab
