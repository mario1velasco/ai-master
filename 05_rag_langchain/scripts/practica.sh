#!/usr/bin/env bash
# Abre JupyterLab en practica/Recursos usando el .venv común y SOLO el .env de la práctica.
# No exporta el .env raíz: así OPENAI_API_KEY es la clave de la práctica (EBIS) y no la personal.
# Uso: scripts/practica.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || { echo "Falta $ROOT/.venv (ver CLAUDE.md)." >&2; exit 1; }
unset OPENAI_API_KEY PINECONE_API_KEY GOOGLE_API_KEY COHERE_API_KEY OPENAI_CHAT_MODEL OPENAI_EMBEDDING_MODEL EMBEDDING_PROVIDER
export PATH="$ROOT/.venv/bin:$PATH"
cd "$ROOT/practica/Recursos "
exec python -m jupyterlab
