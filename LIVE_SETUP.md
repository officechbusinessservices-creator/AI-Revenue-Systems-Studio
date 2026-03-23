# CompliCore — Live Setup Guide

Getting from "runs on seed data" to "runs on real data."
Each step takes 2-5 minutes and immediately unlocks a set of agent capabilities.

---

## The Activation Stack

Work through this in order. Each layer builds on the prior one.

```
LAYER 1 — Anthropic API key    → All 46 AI skills generate live output
LAYER 2 — Gmail + Notion MCPs  → COO agents can read/draft emails and log to databases
LAYER 3 — Stripe MCP + key     → CFO agents read real subscription and invoice data
LAYER 4 — GitHub token         → CTO agents read real PRs, create real issues
LAYER 5 — Sheets + Slack MCPs  → All agents can log metrics and post summaries
LAYER 6 — Telegram bot         → CEO/CTO approval notifications go to your phone
```

---

## Layer 1 — Anthropic API Key

**What it unlocks:** Every AI skill switches from seed data to live generation.

```bash
# 1. Get your key
open https://console.anthropic.com/account/keys

# 2. Add to .env.local
echo 'ANTHROPIC_API_KEY=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' >> .env.local

# 3. Verify
python scripts/go_live.py --connector anthropic
```

Expected output: `✓ Anthropic API: model=claude-sonnet-4-6 · 1.2s`

**What changes immediately:** Devil's Advocate tests, competitor flanking maps, positioning builders, content calendars, viral hooks, video scripts — all switch from template output to AI-generated analysis.

---

## Layer 2 — Gmail + Notion MCPs

**What it unlocks:** COO agents can read real support emails, draft real replies, and log everything to real Notion databases.

### Gmail

```
1. Go to: claude.ai → Settings → Integrations
2. Click "Connect" next to Gmail
3. Authorize with your Google account
4. Gmail is now accessible via MCP
```

### Notion

```
1. Go to: claude.ai → Settings → Integrations
2. Click "Connect" next to Notion
3. Authorize and select which workspaces to share
4. Add these database IDs to .env.local:
```

```bash
# Find database IDs in Notion URLs:
# https://notion.so/workspace/XXXXXXXX = the ID

# Create these 4 databases in Notion first (or use existing ones):
NOTION_CLIENTS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_SUPPORT_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_WEEKLY_REVIEWS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_FEEDBACK_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_CONTENT_CALENDAR_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Test

```bash
python scripts/go_live.py --connector gmail
python scripts/go_live.py --connector notion
```

**What changes:** `coo/support_inbox_zero` now reads real Gmail, classifies real emails, and creates real Gmail drafts. `coo/client_onboarding` creates real Notion client pages. `coo/weekly_business_review` logs to real Notion databases.

---

## Layer 3 — Stripe

**What it unlocks:** CFO agents read real MRR, invoice, and subscription data.

### Stripe MCP (read-only, recommended)

```
1. Go to: claude.ai → Settings → Integrations
2. Click "Connect" next to Stripe
3. Authorize with your Stripe account (read-only scope)
```

### Stripe API Key (for webhooks)

```bash
# Live key for production:
STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE

# Webhook secret (from Stripe Dashboard → Webhooks):
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE

# Publishable key for frontend:
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE
```

### Test

```bash
python scripts/go_live.py --connector stripe
```

**What changes:** `cfo/mrr_dashboard` reads real Stripe subscription data and computes real MRR decomposition. `cfo/invoice_chaser` reads real overdue invoices and drafts real reminders. Stripe webhooks process real payment events.

---

## Layer 4 — GitHub (CTO Agent)

**What it unlocks:** CTO agents monitor real repository activity.

```bash
# 1. Create Personal Access Token
open https://github.com/settings/tokens/new

# Required scopes: repo (read), issues (write)

# 2. Add to .env.local
GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE
GITHUB_REPO=your-org/complicore

# 3. Test
python scripts/go_live.py --connector github
```

**What changes:** `cto/changelog_generator` reads real merged PRs. `cto/bug_report_to_issue` creates real GitHub issues. `cto/weekly_ship_report` reports real velocity. `cto/uptime_error_check` monitors real GitHub Actions.

---

## Layer 5 — Google Sheets + Slack MCPs

**What it unlocks:** Metric logging and team notifications.

### Google Sheets

```
1. Go to: claude.ai → Settings → Integrations → Connect Google Sheets
2. Create these spreadsheets (or use existing):
```

```bash
# Add spreadsheet IDs to .env.local (from spreadsheet URL):
GSHEETS_REVENUE_TRACKER_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GSHEETS_EXPENSE_LOG_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GSHEETS_SAAS_AUDIT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Slack

```
1. Go to: claude.ai → Settings → Integrations → Connect Slack
2. Authorize and select workspace
3. Add channel names to .env.local:
```

```bash
SLACK_OPS_DAILY_CHANNEL=#ops-daily
SLACK_OPS_WEEKLY_CHANNEL=#ops-weekly
SLACK_FINANCE_CHANNEL=#finance
SLACK_ALERTS_CHANNEL=#ops-alerts
SLACK_MARKETING_CHANNEL=#marketing
```

**What changes:** All agents log metrics to real Sheets. Slack receives daily summaries: COO support digest, CFO MRR summary, CTO uptime alerts, CRO pipeline brief.

---

## Layer 6 — Telegram (Approval Notifications)

**What it unlocks:** Agents text you for approval instead of silently queuing.

```bash
# 1. Create bot
# Open Telegram → search @BotFather → /newbot → follow prompts

# 2. Get your chat ID
# Message @userinfobot in Telegram → it replies with your chat ID

# 3. Add to .env.local
TELEGRAM_BOT_TOKEN=123456:ABCdef...
TELEGRAM_CHAT_ID=your_numeric_chat_id

# 4. Test
python scripts/go_live.py --connector telegram
```

**What changes:** When agents create Gmail drafts, post content, or take any approved action — they text you first. You reply "yes" to approve. 30-second timeout with configurable auto-behavior.

---

## Using Live Handlers

The `apps/mcp/live/` directory contains production-grade handlers that use the MCP bridge. To activate them:

```python
# In your orchestrator or skill handler, swap the import:

# Before (seed data):
from plugins.role_coo.skills.support_inbox_zero.handler import run

# After (live data via MCP bridge):
from apps.mcp.live.coo_support_inbox_zero import run
```

Or trigger directly for testing:

```bash
python -c "
import asyncio
from apps.mcp.live.coo_support_inbox_zero import run
result = asyncio.run(run({'workspace': 'complicore', 'dry_run': True}))
print(result)
"
```

---

## Full Live Validation

Once all layers are configured, run the complete validator:

```bash
python scripts/go_live.py --fix-hints
```

Expected output when fully live:

```
✓ Anthropic API: model=claude-sonnet-4-6 · 1.1s
✓ Database: PostgreSQL 16.x
✓ Redis: connected
✓ Gmail MCP: reachable · 12 tool calls
✓ Notion MCP: reachable · 8 tool calls
✓ Sheets MCP: reachable · 6 tool calls
✓ Slack MCP: reachable · 4 tool calls
✓ GitHub Token: authenticated as @your-handle · repo=your-org/complicore
✓ Stripe Key: authenticated · mode=LIVE
✓ Telegram: bot @your_bot · chat_id=set

LIVE READINESS: READY ✓
```

---

## Trigger a Live End-to-End Test

```bash
# Test the full COO → Gmail → Notion → Slack pipeline
python -c "
import asyncio
from apps.mcp.live.coo_client_onboarding import run
result = asyncio.run(run({
    'workspace':  'complicore',
    'user_id':    'test-001',
    'email':      'your-test@email.com',
    'name':       'Test User',
    'plan_id':    'host_club',
    'dry_run':    True,    # Set False to actually create drafts
}))
import json
print(json.dumps(result, indent=2))
"
```

Expected: Gmail draft created + Notion page created + Slack message posted.

---

## What Each Agent Does Live

| Agent | Live Data Source | Live Outputs |
|---|---|---|
| COO | Gmail inbox (real emails) | Gmail drafts, Notion pages, Slack summaries |
| CFO | Stripe (real subscriptions) | MRR dashboard in Sheets, invoice reminders in Gmail |
| CMO | Notion content calendar | X and LinkedIn drafts queued for approval |
| CTO | GitHub PRs + Actions | Changelogs, GitHub issues, Slack alerts |
| CRO | Sheets pipeline tracker | Velocity reports, outreach templates |
| CEO | All 5 agent outputs | Weekly brief in Notion, Slack announcement |

---

## Approval Flow Live

When `LIVE_TRADING=true` (or for any agent external action):

1. Agent completes analysis → creates `approval_required: true` output
2. Telegram message sent: `🎯 TRADE SIGNAL [id]` or `⚠️ APPROVAL REQUIRED: send email to X`
3. You reply `yes` within 30 seconds (configurable)
4. Action executes
5. If no reply within 30s: auto-skip (configurable to auto-execute)

Set `AUTO_EXECUTE_ON_TIMEOUT=true` only when you fully trust the agent's judgment for that workflow.
