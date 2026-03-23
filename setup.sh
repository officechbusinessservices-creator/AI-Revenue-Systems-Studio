#!/usr/bin/env bash
# =============================================================================
# CompliCore — setup.sh
# One command: configure → infra → database → workers → validate
#
# Usage: chmod +x setup.sh && ./setup.sh
#        ./setup.sh --skip-docker    (if infra already running)
#        ./setup.sh --validate-only  (just run health checks)
# =============================================================================
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"
CYAN="\033[36m"; BOLD="\033[1m"; RESET="\033[0m"

step()  { echo -e "\n${CYAN}${BOLD}▶ $1${RESET}"; }
ok()    { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
fail()  { echo -e "  ${RED}✗${RESET} $1"; }
die()   { fail "$1"; exit 1; }

SKIP_DOCKER=false
VALIDATE_ONLY=false
for arg in "$@"; do
  [[ "$arg" == "--skip-docker" ]]   && SKIP_DOCKER=true
  [[ "$arg" == "--validate-only" ]] && VALIDATE_ONLY=true
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo -e "\n${BOLD}CompliCore — Platform Setup${RESET}"
echo -e "Root: $ROOT"
echo "$(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "======================================================"

# ── 0. Validate-only mode ────────────────────────────────────────────────────
if $VALIDATE_ONLY; then
  step "Skill Validation"
  source .venv/bin/activate 2>/dev/null || die "No .venv found — run setup.sh first"
  python scripts/validate_skills.py
  exit $?
fi

# ── 1. Prerequisites check ────────────────────────────────────────────────────
step "Checking prerequisites"
command -v python3 >/dev/null 2>&1 && ok "Python $(python3 --version 2>&1 | cut -d' ' -f2)" || die "Python 3.11+ required"
command -v node    >/dev/null 2>&1 && ok "Node $(node --version)"                              || die "Node 20+ required"
command -v docker  >/dev/null 2>&1 && ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')" || die "Docker required"

# Check Python version
PY_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
[[ $PY_VERSION -ge 11 ]] && ok "Python 3.$PY_VERSION ≥ 3.11" || warn "Python 3.$PY_VERSION — recommend 3.11+"

# ── 2. Environment configuration ─────────────────────────────────────────────
step "Environment configuration"
if [[ ! -f ".env.local" ]]; then
  cp .env.local.example .env.local
  warn ".env.local created from template — EDIT IT before proceeding"
  warn "Minimum required: ANTHROPIC_API_KEY, DATABASE_URL"
  echo ""
  read -p "  Press Enter after editing .env.local, or Ctrl+C to abort..."
else
  ok ".env.local exists"
fi

# Check critical env vars
source .env.local 2>/dev/null || true
[[ -n "${ANTHROPIC_API_KEY:-}" ]] && ok "ANTHROPIC_API_KEY set" || warn "ANTHROPIC_API_KEY not set — AI skills will use seed data"
[[ -n "${DATABASE_URL:-}" ]]       && ok "DATABASE_URL set"      || warn "DATABASE_URL not set — using default localhost"
[[ -n "${REDIS_URL:-}" ]]          && ok "REDIS_URL set"         || ok "REDIS_URL not set — defaulting to redis://localhost:6379"

# ── 3. Python environment ─────────────────────────────────────────────────────
step "Python environment"
if [[ ! -d ".venv" ]]; then
  echo "  Creating virtualenv..."
  python3 -m venv .venv
  ok "Virtualenv created at .venv/"
else
  ok ".venv/ exists"
fi

source .venv/bin/activate
echo "  Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt && ok "Python dependencies installed" || warn "Some dependencies failed — check requirements.txt"

# ── 4. Infrastructure ─────────────────────────────────────────────────────────
if ! $SKIP_DOCKER; then
  step "Starting infrastructure (Docker)"
  docker compose up -d postgres redis qdrant temporal temporal-ui 2>/dev/null || \
    docker-compose up -d postgres redis qdrant temporal temporal-ui 2>/dev/null || \
    warn "Docker Compose failed — ensure docker-compose.yml is present"

  echo "  Waiting for services to become healthy (30s)..."
  sleep 8

  # Health checks
  for service in postgres redis; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' "complicore-${service}" 2>/dev/null || echo "unknown")
    [[ "$STATUS" == "healthy" ]] && ok "$service healthy" || warn "$service status: $STATUS"
  done
else
  ok "Skipping Docker (--skip-docker)"
fi

# ── 5. Database ───────────────────────────────────────────────────────────────
step "Database initialization"
if [[ -d "backend" ]]; then
  cd backend
  [[ ! -d "node_modules" ]] && npm install --silent
  npx prisma generate --silent 2>/dev/null && ok "Prisma client generated" || warn "Prisma generate failed"
  npx prisma migrate deploy 2>/dev/null   && ok "Migrations applied"       || warn "Migrations failed (may need DATABASE_URL)"
  npm run seed 2>/dev/null                && ok "Database seeded"          || warn "Seed failed (non-fatal if already seeded)"
  cd ..
else
  warn "backend/ directory not found — skipping database init"
fi

# ── 6. Platform validation ────────────────────────────────────────────────────
step "Platform validation (46 skills × 85 checks)"
python scripts/validate_skills.py
VALIDATE_EXIT=$?
[[ $VALIDATE_EXIT -eq 0 ]] && ok "All skill checks passed" || warn "Some warnings detected — check output above"

# ── 7. Worker startup ─────────────────────────────────────────────────────────
step "Starting agent workers"
chmod +x scripts/start_workers.sh scripts/stop_workers.sh scripts/worker_status.sh
./scripts/start_workers.sh
sleep 3
./scripts/worker_status.sh

# ── 8. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo -e "${BOLD}${GREEN}Setup Complete${RESET}"
echo "======================================================"
echo ""
echo "  Start frontend:    npm run dev"
echo "  Start backend:     cd backend && npm run dev"
echo ""
echo "  Agent Control:     http://localhost:3000/agent-control"
echo "  Temporal UI:       http://localhost:8080"
echo "  Grafana:           http://localhost:3001  (admin / complicore)"
echo ""
echo "  Stop agents:       ./scripts/stop_workers.sh"
echo "  Check status:      ./scripts/worker_status.sh"
echo "  Validate:          python scripts/validate_skills.py"
echo ""
[[ -z "${ANTHROPIC_API_KEY:-}" ]] && echo -e "  ${YELLOW}⚠${RESET}  Set ANTHROPIC_API_KEY in .env.local to enable full AI skill execution"
[[ -z "${GITHUB_TOKEN:-}" ]]      && echo -e "  ${YELLOW}⚠${RESET}  Set GITHUB_TOKEN in .env.local for CTO changelog + bug-to-issue skills"
echo ""
