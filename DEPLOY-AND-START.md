# Deploy and Start

This project is now runnable as an operations kit.

## Quick start (recommended)

```bash
./start.sh <client_slug> [output_dir]
```

This command bootstraps + validates the client workspace in one step.

---

## 1) Deploy (initialize a client workspace)

Run:

```bash
./scripts_bootstrap_client.sh <client_slug> [output_dir]
```

Example:

```bash
./scripts_bootstrap_client.sh acme-plumbing clients
```

This creates a ready-to-fill client workspace with all required templates mapped by phase.

---

## 2) Start execution

- Open `START-HERE.md`
- Follow the phase checklist
- Work inside your generated client folder under `clients/<client_slug>/`

Recommended starting files:
- `01-intake/client-intake-form.md`
- `01-intake/access-checklist.md`
- `02-discovery/discovery-workflow-map.md`
- `05-reporting/kpi-scorecard.md`

---

## 3) Validate workspace

Run:

```bash
./scripts/validate_client_workspace.sh clients/<client_slug>
```

Use this before kickoff and before handoff to ensure required artifacts exist.

---

## 4) Daily operator loop

- Update QA progress in `04-qa/qa-launch-checklist.md`
- Update KPI movement in `05-reporting/kpi-scorecard.md`
- Send weekly updates from `05-reporting/weekly-client-report.md`
- Prepare closeout from `06-handoff/handoff-package.md`

---

## 5) Convert to retainer

Use:
- `templates/retainer-renewal-summary.md`

to present KPI movement, wins, next 30-day plan, and commercial terms.
