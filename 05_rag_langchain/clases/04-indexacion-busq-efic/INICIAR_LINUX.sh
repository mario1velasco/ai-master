#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv python install 3.11
uv venv --python 3.11 --clear
uv pip install -r requirements.txt
uv run python verificar_entorno.py
uv run jupyter lab indexacion_busqueda_vectorial_eficiente.ipynb
