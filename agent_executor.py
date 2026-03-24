"""
agent_executor.py — CompliCore Super-Agent AI Execution Engine
==============================================================
Maps each of the 6 CompliCore agents (CEO / CFO / CMO / COO / CRO / CTO)
to their relevant skill context from the .agents/skills/ library and
executes real Claude API calls for every workflow trigger.

Usage (called from app.py):
    from agent_executor import execute_workflow
    result = await execute_workflow(role, workflow, payload)
"""
from __future__ import annotations

import os
import pathlib
import asyncio
from typing import Any

# ── Skill context loader ───────────────────────────────────────────────────────

SKILLS_DIR = pathlib.Path(__file__).parent / ".agents" / "skills"

def _ascii_safe(text: str) -> str:
    """Replace non-ASCII characters to avoid UnicodeEncodeError on systems
    with non-UTF8 locale (e.g. Railway with LANG=C)."""
    return text.encode("ascii", errors="replace").decode("ascii")


def _load_skill(name: str, max_chars: int = 1200) -> str:
    """Load condensed skill context from a SKILL.md file."""
    skill_path = SKILLS_DIR / name / "SKILL.md"
    if not skill_path.exists():
        return ""
    text = skill_path.read_text(encoding="utf-8", errors="replace")
    # Strip YAML front-matter (--- ... ---)
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
            start = end + 1
        except ValueError:
            start = 0
    body = "\n".join(lines[start:]).strip()
    # Sanitize to ASCII and return first max_chars chars for context budget
    return _ascii_safe(body)[:max_chars]


def _build_skill_context(skill_names: list[str]) -> str:
    """Concatenate skill excerpts into a compact context block."""
    parts = []
    for name in skill_names:
        text = _load_skill(name)
        if text:
            parts.append(f"### Skill: {name}\n{text}")
    return "\n\n".join(parts)


# ── Agent personas ─────────────────────────────────────────────────────────────

AGENT_PERSONAS: dict[str, dict] = {
    "ceo": {
        "label": "Chief Executive Officer",
        "persona": (
            "You are the CompliCore CEO agent — a strategic AI executive for the StayOps "
            "furnished-rental platform. You synthesise market intelligence, investor signals, "
            "and company performance into crisp executive decisions. You speak in clear, "
            "confident prose suitable for a board update or investor memo. Every output you "
            "produce is concise, data-anchored, and action-oriented."
        ),
        "skills": ["deep-research", "investor-materials", "market-research", "strategic-compact"],
    },
    "cfo": {
        "label": "Chief Financial Officer",
        "persona": (
            "You are the CompliCore CFO agent — a precision finance AI for the StayOps "
            "furnished-rental platform. You track MRR, churn, billing disputes, cash burn, "
            "and runway. You produce financial snapshots that highlight variances, risks, and "
            "the single most important number to watch. Output in the terse style of a "
            "seasoned finance operator: metric → delta → interpretation → recommendation."
        ),
        "skills": ["deep-research", "investor-materials", "strategic-compact"],
    },
    "cmo": {
        "label": "Chief Marketing Officer",
        "persona": (
            "You are the CompliCore CMO agent — a growth and content AI for the StayOps "
            "furnished-rental platform. You craft platform-native content (X/LinkedIn/email), "
            "run competitive audits, and optimise acquisition funnels. Your copy is sharp, "
            "hook-first, and always adapted to the platform. You reason like a performance "
            "marketer but write like a creative director."
        ),
        "skills": ["content-engine", "market-research", "x-api", "deep-research"],
    },
    "coo": {
        "label": "Chief Operating Officer",
        "persona": (
            "You are the CompliCore COO agent — an operations AI for the StayOps "
            "furnished-rental platform. You manage guest support inbox zero, property "
            "onboarding checklists, supply chain tasks, and SLA adherence. Your outputs are "
            "structured, process-driven, and always include a clear next action. You escalate "
            "edge cases with full context rather than guessing."
        ),
        "skills": ["backend-patterns", "api-design", "verification-loop", "coding-standards"],
    },
    "cro": {
        "label": "Chief Revenue Officer",
        "persona": (
            "You are the CompliCore CRO agent — a revenue growth AI for the StayOps "
            "furnished-rental platform. You optimise upsell funnels, corporate-client "
            "outreach, renewal rates, and pipeline velocity. You produce revenue plays: "
            "specific segments to target, messaging to use, and expected yield. Every "
            "recommendation is tied to a dollar outcome."
        ),
        "skills": ["market-research", "content-engine", "deep-research", "investor-outreach"],
    },
    "cto": {
        "label": "Chief Technology Officer",
        "persona": (
            "You are the CompliCore CTO agent — a technical AI for the StayOps "
            "furnished-rental platform. You monitor uptime, review error logs, audit API "
            "integrations, enforce security best practices, and plan infrastructure changes. "
            "You think in systems: identify root causes, model failure modes, and propose "
            "the minimal fix with highest reliability gain. Output in engineer-to-engineer "
            "style: terse, precise, no fluff."
        ),
        "skills": ["backend-patterns", "api-design", "security-review", "verification-loop", "coding-standards"],
    },
}


# ── Workflow → task description mapping ──────────────────────────────────────

WORKFLOW_TASKS: dict[str, str] = {
    # CFO
    "mrr_dashboard":           "Generate a concise MRR dashboard update. Include current MRR, month-over-month delta, churn risk signals, and one recommended action. Assume current MRR ~$18,240.",
    "billing_dispute_handler": "A billing dispute has been flagged. Draft a structured dispute response: acknowledge the issue, state the resolution steps, and give a 48-hour timeline. Keep it under 80 words.",
    "cashflow_forecast":       "Produce a 30-day cash-flow outlook for StayOps. State key inflows (bookings, corporate contracts), outflows (host payouts, ops costs), and net runway signal.",
    "churn_risk_scan":         "Scan churn risk signals for StayOps subscribers. Identify the top 2-3 risk factors this month and recommend one retention lever per factor.",

    # CMO
    "social_content_pipeline": "Generate 3 ready-to-post social items for StayOps: one X/Twitter thread hook, one LinkedIn post, and one short email subject line. Topic: premium furnished rentals for corporate travellers.",
    "seo_audit":               "Produce a 5-point SEO action plan for StayOps targeting corporate furnished-rental keywords. Include priority, expected impact, and effort for each item.",
    "email_campaign":          "Draft a high-converting email subject + preview text + 3-sentence body for a StayOps corporate outreach campaign. Goal: book a discovery call.",
    "competitor_analysis":     "Identify 3 direct competitors to StayOps in the furnished-rental market. For each: key differentiator, pricing signal, and one weakness StayOps can exploit.",

    # COO
    "support_inbox_zero":      "A guest support queue has 12 open tickets. Draft a triage playbook: categorise ticket types, assign response SLAs, and provide a template reply for the most common issue (check-in instructions).",
    "client_onboarding":       "A new corporate client (TechCorp, 20 employees, monthly stays) has signed. Draft the onboarding welcome message and a 5-step first-week checklist.",
    "property_audit":          "Conduct a virtual property audit checklist for a StayOps listing. List 10 items to verify (safety, amenities, photos, pricing) and flag any common compliance gaps.",
    "supply_chain_review":     "Review the StayOps supply chain for a furnished rental unit. Identify the top 3 procurement risks (cleaning supplies, linens, toiletries) and propose one mitigation per risk.",

    # CRO
    "upsell_pipeline":         "Identify the top 3 upsell opportunities for existing StayOps clients. For each: target segment, offer, expected ARR lift, and one-line pitch.",
    "corporate_outreach":      "Draft a 5-sentence cold outreach message to a Fortune-500 HR/Relocation manager pitching StayOps corporate housing. Include a clear CTA.",
    "renewal_forecast":        "Forecast renewal likelihood for StayOps corporate accounts. Assume 80% base renewal rate. Identify 2 signals that would move an account to high-risk and propose intervention scripts.",
    "pipeline_velocity":       "Analyse StayOps revenue pipeline velocity. Assume 14.2 days average deal cycle. Identify 2 bottlenecks and recommend one action to cut cycle time by 20%.",

    # CTO
    "uptime_error_check":      "Uptime monitoring scan complete. Draft an incident-review summary: current status (all green assumed), last 3 notable events, and one proactive reliability improvement to ship this sprint.",
    "api_integration_audit":   "Audit the StayOps API integrations (booking engine, payment processor, comms layer). Flag the top 3 security or reliability risks and propose a fix for each.",
    "security_review":         "Run a security review checklist for the StayOps platform. Cover auth, secrets management, input validation, and third-party dependencies. Surface the top finding with a severity rating.",
    "infrastructure_plan":     "Plan a Q2 infrastructure upgrade for StayOps. Recommend changes to hosting, database scaling, and monitoring stack. Estimate effort and priority for each.",

    # CEO
    "board_update":            "Draft a 5-bullet board update for StayOps. Cover: MRR, growth rate, top risk, product milestone, and one ask from the board.",
    "investor_memo":           "Write a 3-paragraph investor memo update for StayOps. Tone: transparent and confident. Cover current traction, one challenge being addressed, and the 90-day focus.",
    "strategic_review":        "Conduct a strategic quarterly review for StayOps. Assess: market position, competitive moat, team capacity, and one strategic bet to double down on.",
    "okr_update":              "Generate Q2 OKR progress update for StayOps. Create 3 Objectives with 2 Key Results each. Mark hypothetical progress (0–100%) and surface blockers.",
}

# ── Model selection ────────────────────────────────────────────────────────────

COMPLEX_WORKFLOWS = {
    "board_update", "investor_memo", "strategic_review", "cashflow_forecast",
    "competitor_analysis", "api_integration_audit", "security_review",
    "infrastructure_plan", "okr_update",
}

def _select_model(workflow: str) -> str:
    if workflow in COMPLEX_WORKFLOWS:
        return "claude-sonnet-4-6"
    return "claude-haiku-4-5-20251001"


# ── Core executor ─────────────────────────────────────────────────────────────

async def execute_workflow(
    role: str,
    workflow: str,
    payload: dict[str, Any] | None = None,
) -> str:
    """
    Execute a CompliCore agent workflow using the real Claude API.

    Returns a 1-3 sentence result string suitable for dashboard display.
    Falls back gracefully if ANTHROPIC_API_KEY is not set or API call fails.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return f"[seed mode] {workflow} dispatched — set ANTHROPIC_API_KEY for live AI output."

    agent = AGENT_PERSONAS.get(role)
    if not agent:
        return f"Unknown agent role: {role}"

    task = WORKFLOW_TASKS.get(
        workflow,
        f"Execute the '{workflow}' workflow for the StayOps furnished-rental platform. "
        "Provide a concise, actionable result in 1-3 sentences."
    )

    skill_names = agent["skills"]
    skill_context = _build_skill_context(skill_names)

    # Build system prompt
    system_prompt = f"""{agent['persona']}

## Your Active Skill Context
{skill_context}

## Output Instructions
- Respond in 1-3 short paragraphs maximum.
- Be specific and use concrete numbers where applicable.
- Avoid preamble like "As the CFO agent…" — jump straight into the result.
- Format for a real-time dashboard: scannable, crisp, no markdown headers unless they aid clarity.
"""

    # Build user message
    extra_context = ""
    if payload:
        extra_ctx_parts = [f"{k}: {v}" for k, v in payload.items() if v and k != "workspace"]
        if extra_ctx_parts:
            extra_context = "\n\nAdditional context: " + " | ".join(extra_ctx_parts)

    user_message = task + extra_context

    # Execute API call in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _call_claude, api_key, system_prompt, user_message, workflow)
    return result


def _call_claude(api_key: str, system_prompt: str, user_message: str, workflow: str) -> str:
    """
    Synchronous Claude API call via raw httpx (runs in thread pool).

    Uses the Anthropic Messages REST API directly to avoid SDK version
    compatibility issues (anthropic==0.28.0 conflicts with newer httpx).
    """
    try:
        import httpx
        import json as _json

        model = _select_model(workflow)

        payload = {
            "model": model,
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                content=_json.dumps(payload, ensure_ascii=True).encode("ascii"),
            )

        if response.status_code != 200:
            err = response.json().get("error", {}).get("message", response.text[:120])
            return f"[API {response.status_code}] {err}"

        data = response.json()
        text = data["content"][0]["text"].strip()
        # Truncate to 400 chars for dashboard display
        if len(text) > 400:
            text = text[:397] + "..."
        return text

    except Exception as exc:
        err_type = type(exc).__name__
        return f"[{err_type}] Agent execution issue — check ANTHROPIC_API_KEY and retry."


# ── Skill direct-run ──────────────────────────────────────────────────────────

async def run_skill_direct(
    role: str,
    skill: str,
    payload: dict[str, Any] | None = None,
) -> str:
    """
    Run a named skill directly (called from /v1/skills/run).
    Uses the same agent persona + skill context as workflow execution.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return f"[seed mode] Skill '{skill}' called — set ANTHROPIC_API_KEY for live output."

    agent = AGENT_PERSONAS.get(role, AGENT_PERSONAS["ceo"])

    # Load the specific skill plus the agent's default skills
    all_skills = list(dict.fromkeys([skill] + agent["skills"]))  # deduplicated, skill first
    skill_context = _build_skill_context(all_skills)

    task_description = (payload or {}).get("task") or (
        f"Execute the '{skill}' skill for the StayOps furnished-rental platform. "
        "Provide a specific, actionable result."
    )

    system_prompt = f"""{agent['persona']}

## Active Skill Context
{skill_context}

## Output Instructions
Respond with a focused, actionable result. Be concise (1-3 paragraphs).
Use real numbers and specifics. No preamble.
"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _call_claude, api_key, system_prompt, task_description, skill
    )
