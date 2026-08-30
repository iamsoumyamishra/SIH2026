#!/usr/bin/env bash
# Pull the models configured in .env / registry for the Sovereign AI Workbench.
# The system does NOT auto-download models; run this explicitly when you are
# ready to download models onto your machine.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

models=(
  "${OLLAMA_GENERAL_MODEL:-}"
  "${OLLAMA_REASONING_MODEL:-}"
  "${OLLAMA_CODING_MODEL:-}"
  "${OLLAMA_VISION_MODEL:-}"
  "${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}"
)

echo "Pulling models via ${OLLAMA_BASE_URL}..."
for m in "${models[@]}"; do
  if [ -n "$m" ]; then
    echo "==> ollama pull $m"
    ollama pull "$m"
  fi
done

echo "Done. Verify with: ollama list"
