#!/usr/bin/env bash
# Ejecuta los tests de la práctica hasta el paso N (por defecto, todos). Sin red y sin coste.
# Uso: practica/verificar.sh [N]      p. ej.  practica/verificar.sh 5
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$AQUI/../.venv/bin/python"
[ -x "$PY" ] || { echo "Falta el .venv común (ver CLAUDE.md)." >&2; exit 1; }
LIMITE="${1:-99}"
cd "$AQUI"
MODULOS=()
for f in tests/test_paso_*.py; do
  n="$(basename "$f" | sed -E 's/^test_paso_([0-9]+)_.*/\1/')"
  if [ $((10#$n)) -le $((10#$LIMITE)) ]; then MODULOS+=("tests.$(basename "$f" .py)"); fi
done
[ ${#MODULOS[@]} -gt 0 ] || { echo "No hay tests hasta el paso $LIMITE" >&2; exit 1; }
echo "Tests hasta el paso $LIMITE: ${MODULOS[*]}"
exec env -u OPENAI_API_KEY "$PY" -m unittest -v "${MODULOS[@]}"
