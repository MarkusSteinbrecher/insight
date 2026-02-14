#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ "${1:-}" = "serve" ]; then
  echo "Starting Hugo development server..."
  hugo server --source site/ --buildDrafts --navigateToChanged
else
  echo "Building Hugo site..."
  hugo --source site/ --gc --minify
  echo "Build complete. Output in site/public/"
fi
