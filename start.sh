#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <client_slug> [output_dir]"
  echo "Example: $0 acme-plumbing clients"
  exit 1
fi

CLIENT_SLUG="$1"
OUTPUT_DIR="${2:-clients}"
WORKSPACE="${OUTPUT_DIR}/${CLIENT_SLUG}"

./scripts_bootstrap_client.sh "${CLIENT_SLUG}" "${OUTPUT_DIR}"
./scripts/validate_client_workspace.sh "${WORKSPACE}"

echo ""
echo "🚀 Started successfully: ${WORKSPACE}"
echo "Next: open START-HERE.md and begin Phase 1."
