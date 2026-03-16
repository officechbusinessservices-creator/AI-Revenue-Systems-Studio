#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <client_workspace_dir>"
  echo "Example: $0 clients/acme-plumbing"
  exit 1
fi

BASE="$1"

required=(
  "01-intake/client-intake-form.md"
  "01-intake/access-checklist.md"
  "01-intake/client-onboarding-email.md"
  "02-discovery/discovery-workflow-map.md"
  "02-discovery/proposal-scope-guardrails.md"
  "04-qa/qa-launch-checklist.md"
  "05-reporting/kpi-scorecard.md"
  "05-reporting/weekly-client-report.md"
  "05-reporting/retainer-renewal-summary.md"
  "06-handoff/handoff-package.md"
  "README.md"
)

missing=0
for f in "${required[@]}"; do
  if [[ ! -f "${BASE}/${f}" ]]; then
    echo "❌ Missing: ${BASE}/${f}"
    missing=1
  fi
done

if [[ $missing -ne 0 ]]; then
  echo "\nWorkspace validation failed."
  exit 2
fi

echo "✅ Workspace valid: ${BASE}"
