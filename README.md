# CompliCore

**Maximum revenue. Zero compliance headaches. Six autonomous AI agents.**

CompliCore is a short-term rental operations platform where AI agents run your business operations — invoicing, onboarding, content marketing, pipeline management, engineering workflows, and strategic intelligence — continuously, on schedule, without requiring you to remember.

---

## What's Running

```
6 agents × 46 skills × 28 scheduled workflows = your business on autopilot
```

| Agent | Role | Saves | Cadence |
|---|---|---|---|
| **COO** | Onboarding, support inbox, SEO audits, check-ins | $200/mo | Daily + events |
| **CFO** | MRR dashboard, invoice chasing, runway modeling, expense audit | $180/mo | Daily |
| **CMO** | 30-day content calendar, viral hooks, video scripts, competitor watch | $190/mo | Daily |
| **CTO** | SDD architect, TDD enforcement, changelogs, uptime checks | $90/mo | 30min + weekly |
| **CRO** | Pipeline velocity, outreach targets, landing page headlines | Accelerates pipeline | Daily |
| **CEO** | Weekly brief, devil's advocate tests, competitor flanking maps | Prevents expensive mistakes | Weekly |

**Total automated value: ~$660/month per operator, compounding.**

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose v2

### 1. Clone and configure

```bash
git clone https://github.com/your-org/complicore.git
cd complicore
cp .env.local.example .env.local
```

Open `.env.local` and set **at minimum:**
```bash
ANTHROPIC_API_KEY=sk-ant-...          # Required for all AI skills
DATABASE_URL=postgresql://...          # Your Postgres connection
REDIS_URL=redis://localhost:6379       # Cache + job queue
```

### 2. Start infrastructure (one command)

```bash
docker compose up -d postgres redis qdrant temporal
```

Wait ~30 seconds for services to become healthy:
```bash
docker compose ps  # all should show "healthy"
```

### 3. Initialize database

```bash
cd backend
npm install
npx prisma migrate deploy
npm run seed        # loads billing plans
cd ..
```

### 4. Start the agent system

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

./scripts/start_workers.sh
./scripts/worker_status.sh   # confirm all 7 workers RUNNING
```

### 5. Start the application

```bash
# Terminal A — Backend API
cd backend && npm run dev

# Terminal B — Frontend
npm run dev
```

Open **http://localhost:3000**

---

## Verify Everything Works

```bash
# Health check
curl http://localhost:4000/v1/health

# Validate all 46 skill handlers
python scripts/validate_skills.py
# Expected: 69 passed, 0 failed

# Trigger a test workflow
python -c "
import asyncio
from apps.worker.run_orchestrator import enqueue, AgentTask, AgentRole
asyncio.run(enqueue(AgentTask(
    id='test-001',
    role=AgentRole.CFO,
    workflow='mrr_dashboard',
    payload={'workspace': 'complicore'},
)))
print('Task dispatched — check logs/workers/orchestrator.log')
"

# Watch it execute
tail -f logs/workers/orchestrator.log
```

Open **http://localhost:3000/agent-control** to see the Agent Control Panel.

---

## The Agent Control Panel

`/agent-control` — your live operations dashboard.

- **Agents tab**: Real-time status of all 6 agents (idle/running/error)
- **Queue tab**: Active and pending workflow executions
- **Approvals tab**: Actions requiring your sign-off (emails, posts, external sends)
- **History tab**: Complete run log with expandable task results
- **Trigger button**: Dispatch any workflow manually

---

## Pricing Tiers (your revenue model)

| Plan | Price | Properties |
|---|---|---|
| Host Club | $18/property/mo | Up to 10 |
| Host Club + AI | $46/property/mo | Up to 10 + AI pricing |
| Portfolio Pro | $399/mo flat | 15 properties included |
| Enterprise | $888/mo | 25+ properties + white-label |

---

## Connecting AI Skills

The agents are more powerful when connected to real data. Add these environment variables and MCP connectors:

### Essential (agents operate on seed data without these)
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Enables live AI generation for all 46 skills
GITHUB_TOKEN=ghp_...             # CTO: changelog, bug triage, uptime
GITHUB_REPO=your-org/complicore  # CTO: which repo to monitor
```

### MCP Connectors (Settings → Integrations in claude.ai)
Connect these for full agent capability:
- **Gmail** — COO drafts, CFO invoice chasers, CRO outreach
- **Notion** — All agents log and read from Notion databases
- **Google Sheets** — CFO financial tracking, CRO pipeline
- **Slack** — Agent alerts and summaries
- **Stripe** — CFO subscription monitoring

### Optional amplifiers
```bash
TELEGRAM_BOT_TOKEN=...    # CEO/CTO approval notifications (recommended)
TELEGRAM_CHAT_ID=...
CMO_COMPETITOR_HANDLES=guesty,hostaway,lodgify   # CRO: competitor watch
```

---

## Superpowers Integration (Engineering Workflow)

CompliCore ships with full [Superpowers](https://github.com/obra/superpowers) integration for the CTO agent — giving your engineering process the same autonomous capability as your business operations.

```bash
# Install Superpowers in Claude Code
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

The pipeline: **Feature request → SDD Architect → Writing Plans → Subagent execution → TDD → Code Review → Changelog**

Every feature gets: spec with Given/When/Then criteria → atomic tasks → RED/GREEN/REFACTOR enforcement → two-stage review → isolated git worktree.

---

## The Trading Module (Polymarket)

An autonomous Polymarket BTC volatility straddle copy-trader is included at `apps/trading/`.

```bash
# Step 1: Analyze target wallet strategy first
python apps/trading/analyze_wallet.py --address 0xTARGET_WALLET --days 30

# Step 2: Run in paper mode (default — no real money)
TARGET_WALLET_ADDRESS=0x... python apps/trading/run_trader.py

# Step 3: When confident, go live
LIVE_TRADING=true MAX_TRADE_SIZE_USD=5 python apps/trading/run_trader.py
```

**Safety defaults:** paper mode, $10 max per trade, $50 daily loss limit, manual approval required (30s timeout).

See `apps/trading/README.md` for full strategy explanation.

---

## Monitoring

| Dashboard | URL | What it shows |
|---|---|---|
| Agent Control Panel | http://localhost:3000/agent-control | Live agent status, approvals, history |
| Grafana | http://localhost:3001 | System metrics (admin/complicore) |
| Temporal UI | http://localhost:8080 | Workflow execution graph |

---

## Project Structure

```
complicore/
├── apps/
│   ├── worker/          # 7 Python worker processes
│   ├── scheduler/       # 28-entry cron scheduler
│   ├── api/             # FastAPI gateway
│   └── trading/         # Polymarket straddle copy-trader
├── backend/
│   └── src/
│       ├── routes/      # Fastify API routes (incl. payments, orchestrator)
│       └── lib/         # Security, lifecycle email, JWT
├── plugins/
│   ├── role-coo/        # 6 skills: onboarding → local SEO
│   ├── role-cfo/        # 5 skills: MRR → expense organizer
│   ├── role-cmo/        # 11 skills: content calendar → repurposing
│   ├── role-cto/        # 12 skills: SDD → Superpowers pipeline
│   ├── role-cro/        # 6 skills: pipeline → outreach
│   └── role-ceo/        # 6 skills: weekly brief → GTM planner
├── src/
│   ├── app/             # Next.js pages (landing, agent-control)
│   └── components/      # React components (AgentControlPanel)
├── infra/               # Postgres, Temporal, Prometheus, Grafana configs
├── scripts/
│   ├── validate_skills.py   # Platform health check (85 checks)
│   ├── start_workers.sh     # Start all 7 agent workers
│   ├── stop_workers.sh      # Graceful shutdown
│   └── worker_status.sh     # Live health dashboard
├── docs/synthesis/          # Architecture docs, Superpowers integration
├── .superpowers/            # Superpowers auto-skill config
├── .env.local.example       # Complete environment variable reference
├── docker-compose.yml       # 8-service stack
├── requirements.txt         # 50 Python dependencies
└── LAUNCH_CHECKLIST.md      # 75-item go-live gate
```

---

## Operations

```bash
# Start everything
docker compose up -d
./scripts/start_workers.sh

# Status
./scripts/worker_status.sh

# Stop
./scripts/stop_workers.sh

# Validate platform health
python scripts/validate_skills.py

# View logs
tail -f logs/workers/orchestrator.log
tail -f logs/workers/scheduler.log
```

---

## Documentation

| Document | Location |
|---|---|
| Complete platform architecture | `docs/synthesis/PLATFORM_ARCHITECTURE.md` |
| Superpowers integration | `docs/synthesis/SUPERPOWERS_INTEGRATION.md` |
| Worker startup runbook | `docs/operations/worker-layer-startup.md` |
| Launch checklist (75 items) | `LAUNCH_CHECKLIST.md` |
| Environment variables (70+) | `.env.local.example` |

---

## License

MIT — see LICENSE file.

---

*CompliCore is built on the principle that consistency + compounding beats intensity + irregularity at every time horizon beyond 30 days. The agents run consistently. Your business compounds.*
