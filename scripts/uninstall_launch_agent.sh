#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON="${PYTHON:-python3}"

"$PYTHON" "$SCRIPT_DIR/launch_agent.py" uninstall
