#!/bin/sh
# Retro Survivors - play the game in your browser straight from this folder (Linux): ./play_local.sh [port] [--no-browser]
# Needs Python 3. Ctrl+C stops the local server. Runs tools/serve_local.py.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Python 3 was not found (e.g. sudo dnf install python3)." >&2; exit 1; }
exec "$PY" tools/serve_local.py "$@"
