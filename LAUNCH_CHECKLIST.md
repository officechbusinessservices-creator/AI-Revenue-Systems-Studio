# CompliCore — Launch Checklist
## The Go-Live Gate

**Purpose:** Every item below must be checked before complicore.live serves real customers. This list is not aspirational — it is the minimum viable production posture. Incomplete items block launch.

**Status legend:**  `✅ Done` · `🔄 In Progress` · `⬜ Not Started` · `🚫 Blocked`

---

## 1. Infrastructure

| # | Item | Status | Owner |
|---|---|---|---|
| 1.1 | `docker compose up -d` all 8 services healthy | ⬜ | CTO |
| 1.2 | PostgreSQL 16 with SSL enabled (`DB_SSL=true`) | ⬜ | CTO |
| 1.3 | Redis persistent volume mounted and AOF enabled | ⬜ | CTO |
| 1.4 | Qdrant collection `complicore_artifacts` created | ⬜ | CTO |
| 1.5 | Temporal server connected and task queue `orchestrator-queue` registered | ⬜ | CTO |
| 1.6 | Prometheus scraping `localhost:9090/metrics` from backend | ⬜ | CTO |
| 1.7 | Grafana dashboards loading (agents, revenue, system health) | ⬜ | CTO |
| 1.8 | Blue/green deployment config active (`docker-compose.blue.yml`, `.green.yml`) | ⬜ | CTO |

---

## 2. Database

| # | Item | Status | Owner |
|---|---|---|---|
| 2.1 | `npx prisma migrate deploy` runs clean on production DB | ⬜ | CTO |
| 2.2 | `npm run seed` populates billing plans (host_club, host_club_ai, portfolio_pro, enterprise) | ⬜ | CTO |
| 2.3 | All 4 billing plan records in `BillingPlan` table | ⬜ | CTO |
| 2.4 | `DATABASE_URL` uses production credentials (not `complicore:complicore`) | ⬜ | CTO |
| 2.5 | DB connection pool configured: `connection_limit=10` minimum | ⬜ | CTO |

---

## 3. Authentication & Security

| # | Item | Status | Owner |
|---|---|---|---|
| 3.1 | `JWT_SECRET` is 32+ char random hex (not example value) | ⬜ | CTO |
| 3.2 | `NEXTAUTH_SECRET` is 32+ char random hex | ⬜ | CTO |
| 3.3 | `ENCRYPTION_KEY` is 64 char hex for AES-256-GCM field encryption | ⬜ | CTO |
| 3.4 | `COOKIE_SECURE=true` (HTTPS only cookies in production) | ⬜ | CTO |
| 3.5 | `DB_SSL=true` for production database connections | ⬜ | CTO |
| 3.6 | WebAuthn `WEBAUTHN_RP_ID` and `WEBAUTHN_ORIGIN` match production domain | ⬜ | CTO |
| 3.7 | `HONEYTOKEN_RESOURCE_IDS` set to fake resource IDs for intrusion detection | ⬜ | CTO |
| 3.8 | Security audit log path configured and writable (`SECURITY_AUDIT_LOG_PATH`) | ⬜ | CTO |
| 3.9 | `npm audit` passes with 0 critical vulnerabilities | ⬜ | CTO |
| 3.10 | `gitleaks detect` passes — no secrets committed | ⬜ | CTO |
| 3.11 | `SECURITY_SIEM_EXPORT_URL` configured for production audit trail export | ⬜ | CTO |

---

## 4. Stripe & Payments

| # | Item | Status | Owner |
|---|---|---|---|
| 4.1 | `STRIPE_SECRET_KEY` is live key (`sk_live_...`) not test key | ⬜ | CFO |
| 4.2 | `STRIPE_WEBHOOK_SECRET` registered on Stripe Dashboard → Webhooks | ⬜ | CFO |
| 4.3 | Webhook endpoint `POST /v1/payments/webhook` registered in Stripe: `payment_intent.succeeded`, `payment_intent.payment_failed`, `customer.subscription.deleted`, `checkout.session.completed` | ⬜ | CTO |
| 4.4 | All 4 billing plan price IDs created in Stripe and seeded in DB | ⬜ | CFO |
| 4.5 | Test transaction: create PaymentIntent → webhook fires → `Payment.status = paid` | ⬜ | CTO |
| 4.6 | Test cancellation: cancel Stripe subscription → `Subscription.status = cancelled` in DB | ⬜ | CTO |
| 4.7 | Stripe webhook idempotency verified: fire same event twice → no duplicate DB record | ⬜ | CTO |

---

## 5. Agent Platform

| # | Item | Status | Owner |
|---|---|---|---|
| 5.1 | `./scripts/start_workers.sh` starts all 7 processes cleanly | ⬜ | CTO |
| 5.2 | `./scripts/worker_status.sh` shows all 7 workers RUNNING | ⬜ | CTO |
| 5.3 | Orchestrator startup tasks complete (COO weekly_review + CFO mrr_dashboard) | ⬜ | CTO |
| 5.4 | Policy Guard self-test passes: `python apps/worker/run_policy_guard.py` | ⬜ | CTO |
| 5.5 | Memory Manager Qdrant indexing confirmed (check `logs/workers/memory_manager.log`) | ⬜ | CTO |
| 5.6 | Scheduler fires at least 1 workflow successfully (check Temporal UI) | ⬜ | CTO |
| 5.7 | Manual trigger via Agent Control Panel → `/v1/orchestrator/trigger` → task dispatched | ⬜ | CEO |
| 5.8 | Approval flow end-to-end: agent requests approval → dashboard shows item → approve → action executes | ⬜ | CEO |
| 5.9 | `HUMAN_APPROVAL_WEBHOOK` configured (Slack or email endpoint for production approvals) | ⬜ | COO |
| 5.10 | `POLICY_GUARD_STRICT=true` in production (approval required for all external actions) | ⬜ | CTO |

---

## 6. MCP Integrations

| # | Item | Status | Owner |
|---|---|---|---|
| 6.1 | Gmail MCP connected and authenticated in claude.ai Settings → Integrations | ⬜ | COO |
| 6.2 | Notion MCP connected — `NOTION_CLIENTS_DB_ID`, `NOTION_SUPPORT_DB_ID` set | ⬜ | COO |
| 6.3 | Google Sheets MCP connected — revenue tracker and expense log IDs set | ⬜ | CFO |
| 6.4 | Slack MCP connected — `#ops-daily`, `#ops-alerts`, `#finance` channels configured | ⬜ | COO |
| 6.5 | Stripe MCP connected for read-only invoice and subscription data | ⬜ | CFO |
| 6.6 | GitHub MCP / PAT connected — `GITHUB_TOKEN` and `GITHUB_REPO` set | ⬜ | CTO |
| 6.7 | Test each MCP skill stub: COO `client_onboarding` → Gmail draft visible in Drafts | ⬜ | COO |
| 6.8 | Test CFO `mrr_dashboard` → Slack message in `#finance` | ⬜ | CFO |
| 6.9 | Test CTO `uptime_error_check` → result logged, no false alerts | ⬜ | CTO |

---

## 7. Frontend

| # | Item | Status | Owner |
|---|---|---|---|
| 7.1 | `npm run build` completes with 0 TypeScript errors | ⬜ | CTO |
| 7.2 | `npm run test:frontend` passes — all Vitest tests green | ⬜ | CTO |
| 7.3 | `cd backend && npm run test` passes — all backend tests green (including `payments.webhook.test.ts`) | ⬜ | CTO |
| 7.4 | Agent Control Panel loads at `/agent-control` — all 6 agents visible | ⬜ | CTO |
| 7.5 | Host portal `/portal/host` loads without errors | ⬜ | CTO |
| 7.6 | Guest portal `/portal/guest` loads without errors | ⬜ | CTO |
| 7.7 | Corporate portal `/portal/corporate` loads without errors | ⬜ | CTO |
| 7.8 | Dark mode toggle works correctly across all portal pages | ⬜ | CTO |
| 7.9 | Mobile responsive at 375px viewport — no horizontal scroll | ⬜ | CTO |
| 7.10 | `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is live key | ⬜ | CTO |

---

## 8. API & Backend

| # | Item | Status | Owner |
|---|---|---|---|
| 8.1 | `GET /v1/health` returns `{ status: "ok" }` | ⬜ | CTO |
| 8.2 | `GET /v1/billing/plans` returns all 4 plans | ⬜ | CTO |
| 8.3 | Authentication flow: signup → JWT issued → protected route accessible | ⬜ | CTO |
| 8.4 | RBAC: guest cannot access `/v1/payouts` (returns 403) | ⬜ | CTO |
| 8.5 | Rate limiting active: >100 requests/min returns 429 | ⬜ | CTO |
| 8.6 | CORS configured for production domain only | ⬜ | CTO |
| 8.7 | Idempotency plugin active: duplicate `Idempotency-Key` header returns cached response | ⬜ | CTO |
| 8.8 | `POST /v1/orchestrator/trigger` requires `admin` or `host` role | ⬜ | CTO |

---

## 9. Revenue Operations

| # | Item | Status | Owner |
|---|---|---|---|
| 9.1 | CFO `invoice_chaser` test run: drafts created in Gmail (not sent) | ⬜ | CFO |
| 9.2 | CFO `mrr_dashboard` test run: correct MRR computed from active subscriptions | ⬜ | CFO |
| 9.3 | CFO `runway_calculator` test run: three-scenario output with correct arithmetic | ⬜ | CFO |
| 9.4 | COO `client_onboarding` test run: welcome draft in Gmail + Notion page created | ⬜ | COO |
| 9.5 | CRO `pipeline_velocity` test run: at-risk deals surfaced, velocity computed | ⬜ | CRO |
| 9.6 | First real client onboarded: user created → COO agent fires → welcome draft visible | ⬜ | COO |

---

## 10. Compliance & Legal

| # | Item | Status | Owner |
|---|---|---|---|
| 10.1 | Privacy Policy published at `/privacy` | ⬜ | CEO |
| 10.2 | Terms of Service published at `/terms` | ⬜ | CEO |
| 10.3 | Cookie banner functional (auto-declines non-essential cookies) | ⬜ | CTO |
| 10.4 | GDPR data subject request flow documented and tested | ⬜ | COO |
| 10.5 | Stripe data processing agreement signed | ⬜ | CFO |
| 10.6 | PCI-DSS scope confirmed: no raw card data stored in CompliCore DB | ⬜ | CTO |
| 10.7 | SOC2 audit log chain verified: HMAC-linked entries in `security-audit.jsonl` | ⬜ | CTO |

---

## 11. Monitoring & Alerting

| # | Item | Status | Owner |
|---|---|---|---|
| 11.1 | Grafana agent dashboard shows all 6 agents with real data | ⬜ | CTO |
| 11.2 | Slack `#ops-alerts` receives CTO uptime alert on simulated API failure | ⬜ | CTO |
| 11.3 | CFO runway alert fires when `runway_months_base < 6` (test with mock data) | ⬜ | CFO |
| 11.4 | Policy Guard log (`logs/policy_decisions.jsonl`) writing correctly | ⬜ | CTO |
| 11.5 | Worker heartbeats visible in Temporal UI — all 7 workers registered | ⬜ | CTO |
| 11.6 | `LOG_LEVEL=info` in production (not debug — reduces noise and storage cost) | ⬜ | CTO |

---

## 12. Performance

| # | Item | Status | Owner |
|---|---|---|---|
| 12.1 | `npm run build` bundle size: no route over 500KB uncompressed | ⬜ | CTO |
| 12.2 | `GET /v1/health` latency < 50ms under normal load | ⬜ | CTO |
| 12.3 | `/portal/host` initial page load < 3s on 4G (Lighthouse) | ⬜ | CTO |
| 12.4 | Database query plan: `EXPLAIN ANALYZE` on booking and subscription queries — no seq scans on large tables | ⬜ | CTO |
| 12.5 | Redis connection pool not exhausted under concurrent agent workers | ⬜ | CTO |

---

## 13. Backup & Recovery

| # | Item | Status | Owner |
|---|---|---|---|
| 13.1 | PostgreSQL daily backup configured (pg_dump → S3 or equivalent) | ⬜ | CTO |
| 13.2 | Backup restoration tested: restore to point-in-time and verify data integrity | ⬜ | CTO |
| 13.3 | Worker PID files and logs on persistent volume (not container ephemeral FS) | ⬜ | CTO |
| 13.4 | Qdrant collection snapshot scheduled | ⬜ | CTO |

---

## 14. Go-Live Sequence

Execute in this exact order:

```bash
# Day before launch
1. ✅ All checklist items above resolved
2. Run full test suite: npm run test && cd backend && npm run test
3. Deploy to staging; smoke-test all portals and agent workflows
4. Run security check: npm run security-check

# Launch day
5. docker compose up -d   (all 8 services)
6. npx prisma migrate deploy && npm run seed
7. ./scripts/start_workers.sh
8. Verify: ./scripts/worker_status.sh — all RUNNING
9. Manual trigger: POST /v1/orchestrator/trigger { role: "cfo", workflow: "mrr_dashboard" }
10. Confirm: Temporal UI shows completed workflow
11. Flip DNS / CDN to production
12. Monitor: Grafana dashboard for 30 minutes
13. Announce 🚀
```

---

## Completion Gate

**Launch is blocked until all items in sections 1–8 and 10 are** `✅ Done`.

Sections 9, 11, 12, 13 must be `✅ Done` or `🔄 In Progress` with documented mitigation.

Section 14 executes in order on launch day.

---

*Last updated: 2026-03-17 · CompliCore v2.0 Ultimate*
