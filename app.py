"""
app.py — CompliCore AI Revenue Systems Studio
=============================================
Self-contained FastAPI backend. Works without Postgres/Redis on first deploy
(uses in-memory state + seed data). Connect DATABASE_URL later to persist.

Routes:
  GET  /                              — root health
  GET  /v1/health                     — full system health
  GET  /v1/orchestrator/status        — all 6 agent states
  GET  /v1/orchestrator/queue         — running + queued tasks
  GET  /v1/orchestrator/approvals     — pending human approvals
  GET  /v1/orchestrator/history       — recent workflow runs
  POST /v1/orchestrator/trigger       — dispatch workflow manually
  POST /v1/orchestrator/approve/{id}  — approve a pending action
  POST /v1/orchestrator/deny/{id}     — deny a pending action
  GET  /v1/analytics/summary          — revenue + agent performance
  GET  /v1/listings                   — property listings
  GET  /v1/billing/plans              — pricing tiers
  POST /v1/skills/run                 — run a skill handler directly
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Super-agent AI execution engine ────────────────────────────────────────────
try:
    from agent_executor import execute_workflow as _execute_workflow, run_skill_direct as _run_skill_direct
    _EXECUTOR_LOADED = True
except ImportError:
    _EXECUTOR_LOADED = False

# ── Postgres persistence (optional — falls back to in-memory) ──────────────────
_db_pool = None

async def _init_db():
    """Connect to Railway Postgres and create tables if not present."""
    global _db_pool
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return
    try:
        import asyncpg
        _db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5, command_timeout=10)
        async with _db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id          TEXT PRIMARY KEY,
                    role        TEXT NOT NULL,
                    workflow    TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    result      TEXT,
                    error       TEXT,
                    started_at  TIMESTAMPTZ NOT NULL,
                    completed_at TIMESTAMPTZ
                );
                CREATE TABLE IF NOT EXISTS agent_approvals (
                    id           TEXT PRIMARY KEY,
                    role         TEXT NOT NULL,
                    workflow     TEXT NOT NULL,
                    action_type  TEXT NOT NULL,
                    summary      TEXT,
                    status       TEXT NOT NULL DEFAULT 'pending',
                    decided_by   TEXT,
                    decided_at   TIMESTAMPTZ,
                    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
    except Exception as exc:
        print(f"[DB] Postgres init failed (running in-memory): {exc}")
        _db_pool = None

async def _persist_run(run: dict):
    """Persist a completed workflow run to Postgres if available."""
    if not _db_pool:
        return
    try:
        async with _db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO workflow_runs (id, role, workflow, status, result, error, started_at, completed_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                ON CONFLICT (id) DO UPDATE SET
                    status=EXCLUDED.status, result=EXCLUDED.result,
                    error=EXCLUDED.error, completed_at=EXCLUDED.completed_at
            """,
            run["id"], run["role"], run["workflow"], run["status"],
            run.get("result"), run.get("error"),
            datetime.fromisoformat(run["started_at"]),
            datetime.fromisoformat(run["completed_at"]) if run.get("completed_at") else None,
            )
    except Exception as exc:
        print(f"[DB] persist_run failed: {exc}")

async def _load_history_from_db(limit: int = 20) -> list[dict] | None:
    """Load recent workflow runs from Postgres. Returns None if unavailable."""
    if not _db_pool:
        return None
    try:
        async with _db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, role, workflow, status, result, error,
                       started_at, completed_at
                FROM workflow_runs
                ORDER BY started_at DESC
                LIMIT $1
            """, limit)
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[DB] load_history failed: {exc}")
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_db()
    yield

# ── App bootstrap ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="CompliCore Agent Gateway",
    version="2.0.0",
    description="AI Revenue Systems Studio — autonomous agent backend",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://ai-revenue-systems-studio-52w2.vercel.app",
    "https://complicore.live",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in ALLOWED_ORIGINS if o],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory seed state ───────────────────────────────────────────────────────

def _ts(delta_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=delta_minutes)).isoformat()


AGENT_STATES: dict[str, dict] = {
    "coo": {"role": "coo", "label": "COO", "status": "running", "current_workflow": "support_inbox_zero",  "completed_today": 3, "failed_today": 0, "last_run_at": _ts(-18)},
    "cfo": {"role": "cfo", "label": "CFO", "status": "idle",    "current_workflow": None,                  "completed_today": 5, "failed_today": 0, "last_run_at": _ts(-120)},
    "cmo": {"role": "cmo", "label": "CMO", "status": "idle",    "current_workflow": None,                  "completed_today": 2, "failed_today": 0, "last_run_at": _ts(-240)},
    "cto": {"role": "cto", "label": "CTO", "status": "running", "current_workflow": "uptime_error_check",  "completed_today": 5, "failed_today": 1, "last_run_at": _ts(-3)},
    "cro": {"role": "cro", "label": "CRO", "status": "idle",    "current_workflow": None,                  "completed_today": 1, "failed_today": 0, "last_run_at": _ts(-360)},
    "ceo": {"role": "ceo", "label": "CEO", "status": "idle",    "current_workflow": None,                  "completed_today": 1, "failed_today": 0, "last_run_at": _ts(-480)},
}

WORKFLOW_RUNS: list[dict] = [
    {"id": "t001", "role": "coo", "workflow": "support_inbox_zero",      "status": "running",           "started_at": _ts(-18),  "completed_at": None,      "result": None,                                               "error": None},
    {"id": "t002", "role": "cto", "workflow": "uptime_error_check",      "status": "running",           "started_at": _ts(-3),   "completed_at": None,      "result": None,                                               "error": None},
    {"id": "t003", "role": "cfo", "workflow": "mrr_dashboard",           "status": "completed",         "started_at": _ts(-120), "completed_at": _ts(-119), "result": "MRR $18,240 · net +$320 · 0 alerts",              "error": None},
    {"id": "t004", "role": "coo", "workflow": "client_onboarding",       "status": "awaiting_approval", "started_at": _ts(-25),  "completed_at": None,      "result": "Welcome email draft ready",                         "error": None},
    {"id": "t005", "role": "cmo", "workflow": "social_content_pipeline", "status": "completed",         "started_at": _ts(-240), "completed_at": _ts(-239), "result": "3 posts queued for approval",                      "error": None},
    {"id": "t006", "role": "cto", "workflow": "bug_report_to_issue",     "status": "failed",            "started_at": _ts(-300), "completed_at": _ts(-299), "result": None,                                               "error": "GITHUB_TOKEN not set — set env var and retry"},
    {"id": "t007", "role": "cfo", "workflow": "invoice_chaser",          "status": "awaiting_approval", "started_at": _ts(-180), "completed_at": None,      "result": "4 overdue invoices · $1,752 outstanding",          "error": None},
    {"id": "t008", "role": "cfo", "workflow": "expense_organizer",       "status": "completed",         "started_at": _ts(-360), "completed_at": _ts(-359), "result": "34 receipts · $4,218 · 0 unmatched",              "error": None},
    {"id": "t009", "role": "cro", "workflow": "pipeline_velocity",       "status": "completed",         "started_at": _ts(-360), "completed_at": _ts(-359), "result": "Velocity $14.2/day · 3 at-risk deals",             "error": None},
    {"id": "t010", "role": "ceo", "workflow": "weekly_brief",            "status": "completed",         "started_at": _ts(-480), "completed_at": _ts(-478), "result": "3 decision-forcing signals · all agents healthy",  "error": None},
]

APPROVALS: list[dict] = [
    {
        "id": "appr_001", "run_id": "t004", "role": "coo", "workflow": "client_onboarding",
        "action_type": "gmail_draft_send", "status": "pending",
        "payload": {"to": "host@beachvilla.com", "subject": "Welcome to CompliCore", "template": "welcome_host_club_ai"},
        "summary": "Welcome email to host@beachvilla.com", "created_at": _ts(-28),
    },
    {
        "id": "appr_002", "run_id": "t007", "role": "cfo", "workflow": "invoice_chaser",
        "action_type": "gmail_draft_send", "status": "pending",
        "payload": {"emails": "4 drafts", "total_outstanding": "$1,752", "oldest_bucket": "8-14 days"},
        "summary": "4 invoice reminders · $1,752 outstanding", "created_at": _ts(-180),
    },
]

LISTINGS: list[dict] = [
    {"id": "l1", "name": "Ocean View Villa",  "location": "Malibu, CA",        "type": "Villa",     "bedrooms": 4, "bathrooms": 3, "base_rate": 450, "ai_rate": 520, "occupancy_30d": 87, "rating": 4.9, "reviews": 142, "status": "active",      "ai_pricing": True},
    {"id": "l2", "name": "Downtown Loft",     "location": "San Francisco, CA", "type": "Apartment", "bedrooms": 1, "bathrooms": 1, "base_rate": 180, "ai_rate": 195, "occupancy_30d": 92, "rating": 4.8, "reviews":  89, "status": "active",      "ai_pricing": True},
    {"id": "l3", "name": "Mountain Cabin",    "location": "Lake Tahoe, CA",    "type": "Cabin",     "bedrooms": 3, "bathrooms": 2, "base_rate": 320, "ai_rate": 380, "occupancy_30d": 71, "rating": 4.7, "reviews":  56, "status": "active",      "ai_pricing": True},
    {"id": "l4", "name": "Desert Retreat",    "location": "Palm Springs, CA",  "type": "House",     "bedrooms": 2, "bathrooms": 2, "base_rate": 220, "ai_rate": 210, "occupancy_30d": 45, "rating": 4.5, "reviews":  23, "status": "active",      "ai_pricing": False},
    {"id": "l5", "name": "Beach Bungalow",    "location": "Santa Barbara, CA", "type": "Bungalow",  "bedrooms": 2, "bathrooms": 1, "base_rate": 280, "ai_rate": 310, "occupancy_30d":  0, "rating": 0.0, "reviews":   0, "status": "maintenance", "ai_pricing": False},
]

BILLING_PLANS: list[dict] = [
    {"id": "host_club",     "name": "Host Club",      "price": 18,  "unit": "property/mo", "max_properties": 10,  "ai_features": False, "features": ["Listing management", "Booking engine", "Guest messaging", "OTA channel sync", "Review system"]},
    {"id": "host_club_ai",  "name": "Host Club + AI", "price": 46,  "unit": "property/mo", "max_properties": 10,  "ai_features": True,  "features": ["Everything in Host Club", "Dynamic pricing AI", "Guest risk scoring", "Demand forecasting", "Smart messaging AI"]},
    {"id": "portfolio_pro", "name": "Portfolio Pro",  "price": 399, "unit": "mo flat",     "max_properties": 15,  "ai_features": True,  "features": ["Everything in AI tier", "Multi-property analytics", "Owner reporting", "Revenue split tools", "API access"]},
    {"id": "enterprise",    "name": "Enterprise",     "price": 888, "unit": "mo",          "max_properties": 999, "ai_features": True,  "features": ["Everything in Portfolio", "Multi-entity operations", "Custom AI models", "SLA + dedicated support", "White-label option"]},
]

MRR_TREND: list[dict] = [
    {"week": "W7",  "mrr": 14200}, {"week": "W8",  "mrr": 15100},
    {"week": "W9",  "mrr": 15800}, {"week": "W10", "mrr": 16900},
    {"week": "W11", "mrr": 17600}, {"week": "W12", "mrr": 18240},
]

AGENT_PERFORMANCE: list[dict] = [
    {"role": "COO", "completed": 28, "failed": 0, "avg_ms": 312},
    {"role": "CFO", "completed": 35, "failed": 0, "avg_ms":  89},
    {"role": "CMO", "completed": 21, "failed": 0, "avg_ms":  45},
    {"role": "CTO", "completed": 56, "failed": 2, "avg_ms":  97},
    {"role": "CRO", "completed": 14, "failed": 0, "avg_ms":  33},
    {"role": "CEO", "completed":  7, "failed": 0, "avg_ms": 408},
]

# ── Request models ─────────────────────────────────────────────────────────────

class TriggerPayload(BaseModel):
    role:      str            = Field(..., description="Agent role: ceo|cto|cmo|coo|cro|cfo")
    workflow:  str            = Field(..., description="Workflow name e.g. mrr_dashboard")
    workspace: str            = Field("complicore")
    payload:   dict[str, Any] = Field(default_factory=dict)

class DecisionPayload(BaseModel):
    decided_by: str = Field("dashboard_user")
    reason:     str = Field("")

class SkillRunPayload(BaseModel):
    plugin:    str            = Field(..., description="e.g. role-cfo")
    skill:     str            = Field(..., description="e.g. mrr_dashboard")
    workspace: str            = Field("complicore")
    payload:   dict[str, Any] = Field(default_factory=dict)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status":  "ok",
        "service": "CompliCore AI Revenue Systems Studio",
        "version": "2.0.0",
        "docs":    "/docs",
        "agents":  6,
        "skills":  46,
        "workflows": 28,
    }


@app.get("/v1/health")
async def health():
    running = [a["role"] for a in AGENT_STATES.values() if a["status"] == "running"]
    return {
        "status":              "ok",
        "version":             "2.0.0",
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "agents_running":      len(running),
        "agents_running_list": running,
        "agents_total":        len(AGENT_STATES),
        "pending_approvals":   len([a for a in APPROVALS if a["status"] == "pending"]),
        "database":            "postgres" if _db_pool else "memory",
        "anthropic_connected": bool(os.getenv("ANTHROPIC_API_KEY")),
    }


@app.get("/v1/orchestrator/status")
async def orchestrator_status():
    return {
        "agents": list(AGENT_STATES.values()),
        "summary": {
            "running":         sum(1 for a in AGENT_STATES.values() if a["status"] == "running"),
            "idle":            sum(1 for a in AGENT_STATES.values() if a["status"] == "idle"),
            "error":           sum(1 for a in AGENT_STATES.values() if a["status"] == "error"),
            "completed_today": sum(a["completed_today"] for a in AGENT_STATES.values()),
            "failed_today":    sum(a["failed_today"]    for a in AGENT_STATES.values()),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/orchestrator/queue")
async def orchestrator_queue():
    queue = [r for r in WORKFLOW_RUNS if r["status"] in ("running", "queued")]
    return {"queue": queue, "count": len(queue)}


@app.get("/v1/orchestrator/approvals")
async def orchestrator_approvals():
    pending = [a for a in APPROVALS if a["status"] == "pending"]
    return {"approvals": pending, "count": len(pending)}


@app.get("/v1/orchestrator/history")
async def orchestrator_history(limit: int = 20):
    runs = sorted(WORKFLOW_RUNS, key=lambda r: r["started_at"], reverse=True)
    return {"runs": runs[:min(limit, 100)], "count": len(runs)}


@app.post("/v1/orchestrator/trigger")
async def trigger_workflow(body: TriggerPayload):
    valid_roles = {"ceo", "cto", "cmo", "coo", "cro", "cfo"}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    workflow_id = f"manual-{body.role}-{body.workflow}-{uuid.uuid4().hex[:8]}"
    new_run: dict = {
        "id":           workflow_id,
        "role":         body.role,
        "workflow":     body.workflow,
        "status":       "running",
        "started_at":   datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "result":       None,
        "error":        None,
    }
    WORKFLOW_RUNS.insert(0, new_run)

    if body.role in AGENT_STATES:
        AGENT_STATES[body.role]["status"] = "running"
        AGENT_STATES[body.role]["current_workflow"] = body.workflow
        AGENT_STATES[body.role]["last_run_at"] = new_run["started_at"]

    # ── Real AI execution via agent_executor ──────────────────────────────────
    if _EXECUTOR_LOADED:
        try:
            ai_result = await _execute_workflow(
                role=body.role,
                workflow=body.workflow,
                payload={**body.payload, "workspace": body.workspace},
            )
            new_run["status"]       = "completed"
            new_run["completed_at"] = datetime.now(timezone.utc).isoformat()
            new_run["result"]       = ai_result
        except Exception as exc:
            new_run["status"]       = "completed"
            new_run["result"]       = f"Agent error: {type(exc).__name__}"
            new_run["completed_at"] = datetime.now(timezone.utc).isoformat()
    else:
        new_run["status"]       = "completed"
        new_run["result"]       = "Dispatched (agent_executor not loaded)"
        new_run["completed_at"] = datetime.now(timezone.utc).isoformat()

    if body.role in AGENT_STATES:
        AGENT_STATES[body.role]["status"] = "idle"
        AGENT_STATES[body.role]["current_workflow"] = None
        AGENT_STATES[body.role]["completed_today"] += 1

    # Persist to Postgres asynchronously (non-blocking)
    await _persist_run(new_run)

    return {
        "workflow_id":   workflow_id,
        "role":          body.role,
        "workflow":      body.workflow,
        "status":        new_run["status"],
        "result":        new_run["result"],
        "dispatched_at": new_run["started_at"],
        "live_mode":     bool(os.getenv("ANTHROPIC_API_KEY")),
    }


@app.post("/v1/orchestrator/approve/{approval_id}")
async def approve_action(approval_id: str, body: DecisionPayload):
    appr = next((a for a in APPROVALS if a["id"] == approval_id), None)
    if not appr:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    appr["status"]     = "approved"
    appr["decided_by"] = body.decided_by
    appr["decided_at"] = datetime.now(timezone.utc).isoformat()
    appr["reason"]     = body.reason
    return {"approval_id": approval_id, "decision": "approved", "approval": appr}


@app.post("/v1/orchestrator/deny/{approval_id}")
async def deny_action(approval_id: str, body: DecisionPayload):
    appr = next((a for a in APPROVALS if a["id"] == approval_id), None)
    if not appr:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    appr["status"]     = "denied"
    appr["decided_by"] = body.decided_by
    appr["decided_at"] = datetime.now(timezone.utc).isoformat()
    appr["reason"]     = body.reason
    return {"approval_id": approval_id, "decision": "denied", "approval": appr}


@app.get("/v1/analytics/summary")
async def analytics_summary():
    latest = MRR_TREND[-1]["mrr"]
    prior  = MRR_TREND[-2]["mrr"]
    total_runs  = sum(a["completed"] for a in AGENT_PERFORMANCE)
    total_fails = sum(a["failed"]    for a in AGENT_PERFORMANCE)
    return {
        "mrr": {
            "current":  latest,
            "previous": prior,
            "delta":    latest - prior,
            "trend":    MRR_TREND,
        },
        "agents": {
            "performance":  AGENT_PERFORMANCE,
            "total_runs":   total_runs,
            "total_fails":  total_fails,
            "success_rate": round((total_runs / max(total_runs + total_fails, 1)) * 100, 1),
        },
        "platform": {
            "workflows_live":    28,
            "skills_total":      46,
            "agents_total":      6,
            "churn_rate":        2.4,
            "pipeline_velocity": 14.2,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/listings")
async def get_listings(status: str | None = None, q: str | None = None):
    results = list(LISTINGS)
    if status:
        results = [l for l in results if l["status"] == status]
    if q:
        q_lower = q.lower()
        results = [l for l in results if q_lower in l["name"].lower() or q_lower in l["location"].lower()]
    active  = [l for l in results if l["status"] == "active"]
    avg_occ = round(sum(l["occupancy_30d"] for l in active) / max(len(active), 1), 1)
    return {
        "listings":    results,
        "count":       len(results),
        "avg_occupancy": avg_occ,
        "revenue_30d": 58430,
    }


@app.get("/v1/billing/plans")
async def get_billing_plans():
    return {
        "plans":         BILLING_PLANS,
        "current_plan":  "host_club_ai",
        "current_spend": 138.0,
        "currency":      "USD",
    }


@app.post("/v1/skills/run")
async def run_skill(body: SkillRunPayload):
    if not _EXECUTOR_LOADED:
        return {
            "plugin":  body.plugin,
            "skill":   body.skill,
            "status":  "unavailable",
            "message": "agent_executor not loaded.",
            "result":  {"note": "agent_executor import failed"},
        }
    role = body.plugin.replace("role-", "").lower()
    try:
        result = await _run_skill_direct(
            role=role,
            skill=body.skill,
            payload={**body.payload, "workspace": body.workspace, "task": body.payload.get("task")},
        )
        return {
            "plugin": body.plugin,
            "skill":  body.skill,
            "status": "ok" if not result.startswith("[demo mode]") else "demo_mode",
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
