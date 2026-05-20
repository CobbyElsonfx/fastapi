#!/usr/bin/env bash
# Run from ai-service/ directory: ./start.sh
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Create a venv first: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
