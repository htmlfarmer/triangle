#!/usr/bin/env bash
# Wrapper to run the Qibla-Numa report in a terminal window or as a login task.
# Usage: ./run_try.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=python3
"$PYTHON" "$SCRIPT_DIR/try.py"
