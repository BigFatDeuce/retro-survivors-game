#!/bin/sh
# Retro Survivors - builds the playable Windows game from Linux: dist/RetroSurvivors/RetroSurvivors.exe (no zip).
# Needs Python 3 and Internet the first time (Electron, kept in dist/cache); wine is optional (it sets the exe's icon).
# Runs tools/make_exe.py.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Python 3 was not found (e.g. sudo dnf install python3)." >&2; exit 1; }
exec "$PY" tools/make_exe.py "$@"
