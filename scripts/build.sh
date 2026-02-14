#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ "${1:-}" = "serve" ]; then
  echo "Starting local development server on http://localhost:8000..."
  cd docs && python3 -m http.server 8000
else
  echo "Building site data..."
  python3 scripts/build-insights-data.py
  python3 scripts/build-sources-data.py
  echo "Build complete. Site is in docs/"
fi
