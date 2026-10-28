#!/bin/sh
# Retro Survivors - builds the Android APK from Linux: dist/RetroSurvivors-<version>.apk
# Needs Python 3 and Internet the first time (Google's Android build tools after their licence, a JDK if javac is missing:
# kept in dist/cache/android). Signing key: ~/.retro-survivors/android.keystore (keep it). Runs tools/make_apk.py.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Python 3 was not found (e.g. sudo dnf install python3)." >&2; exit 1; }
exec "$PY" tools/make_apk.py "$@"
