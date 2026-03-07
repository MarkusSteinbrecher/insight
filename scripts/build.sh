#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [ "${1:-}" = "serve" ]; then
  echo "Starting local development server on http://localhost:8000..."
  cd docs && python3 -m http.server 8000
elif [ "${1:-}" = "dev" ]; then
  echo "Starting Svelte dev server..."
  cd site && npm run dev -- --open
else
  echo "Building site data..."
  # Graph export (writes JSON to docs/data/)
  python3 -m insight.exporter

  # Copy images to docs for serving
  if [ -d "data/images" ]; then
    mkdir -p docs/data/images
    cp -r data/images/* docs/data/images/ 2>/dev/null || true
  fi

  echo "Build complete. Data is in docs/data/"
fi
