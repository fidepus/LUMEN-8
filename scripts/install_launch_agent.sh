#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PYTHON="${PYTHON:-python3}"

"$PYTHON" "$SCRIPT_DIR/launch_agent.py" install --root "$PROJECT_ROOT"
