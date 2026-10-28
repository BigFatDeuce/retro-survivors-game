#!/bin/sh
# Retro Survivors - builds the Linux AppImage from Linux: dist/RetroSurvivors-<version>-x86_64.AppImage
# Needs Python 3 and Internet the first time (Electron, AppImage tools: kept in dist/cache). Uses mksquashfs when it is
# installed (sudo dnf install squashfs-tools), else downloads the official appimagetool. Runs tools/make_appimage.py.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Python 3 was not found (e.g. sudo dnf install python3)." >&2; exit 1; }
exec "$PY" tools/make_appimage.py "$@"
