# AI Revenue Systems Studio — User-Ready Kit

This repository is a **ready-to-run operating kit** for delivering the AI Revenue Systems Studio offer to service businesses.

## What you get

- A complete offer blueprint (`AI-Revenue-Systems-Studio-Blueprint.md`)
- Implementation templates (`templates/`)
- A step-by-step operator checklist (`START-HERE.md`)
- Client delivery pack structure (`client-delivery-pack/`)

## Start here

1. Open `DEPLOY-AND-START.md`
2. Run `./start.sh <client_slug> [output_dir]`
3. Follow `START-HERE.md` for pre-sales to post-launch execution
4. Deliver and close out using your generated client workspace

## Installation & Setup

To set up this project locally, we recommend using `requirements.lock` for dependency installation. This file contains pre-verified version pins that avoid the pip backtracking and dependency resolution issues noted in `requirements.txt`.

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/officechbusinessservices-creator/AI-Revenue-Systems-Studio.git
cd AI-Revenue-Systems-Studio

# Install dependencies using locked versions
pip install -r requirements.lock
```

### For Local Development (Slower)

If you need to modify dependencies, install from `requirements.txt` instead:

```bash
pip install -r requirements.txt
```

> **Note:** Loose version constraints in `requirements.txt` may cause pip to spend 10+ minutes resolving the grpcio/grpcio-tools/googleapis-common-protos compatibility. Always prefer `requirements.lock` for production and CI/CD builds.

### Build Prerequisites

Some packages require C/C++ build tools:

**On Linux:**
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev libpq-dev
```

**On macOS:**
```bash
brew install python@3.11 postgresql
```

### Troubleshooting

- **Build failures for grpcio, asyncpg, orjson, pydantic-core:** Install build essentials (see above)
- **Long pip install times:** Use `requirements.lock` instead of `requirements.txt`
- **Version conflicts:** Clear pip cache: `pip cache purge` then retry

## Core files

- `AI-Revenue-Systems-Studio-Blueprint.md`
- `DEPLOY-AND-START.md`
- `START-HERE.md`
- `start.sh`
- `scripts_bootstrap_client.sh`
- `scripts/validate_client_workspace.sh`
- `templates/client-intake-form.md`
- `templates/access-checklist.md`
- `templates/discovery-workflow-map.md`
- `templates/kpi-scorecard.md`
- `templates/qa-launch-checklist.md`
- `templates/weekly-client-report.md`
- `templates/handoff-package.md`
- `templates/proposal-scope-guardrails.md`

## License

Internal operating materials. Add your preferred license if publishing externally.