#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Prefer venv if present (for packaged installs), else fall back to system python3
if [[ -f "$SCRIPT_DIR/venv/bin/python3" ]]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python3"
else
    PYTHON="/usr/bin/python3"
fi

cd "$SCRIPT_DIR"
exec "$PYTHON" "$SCRIPT_DIR/scandesk.py" "$@"
