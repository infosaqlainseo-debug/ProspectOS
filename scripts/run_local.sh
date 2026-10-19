#!/usr/bin/env bash
# ==============================================================================
# ProspectOS: Local Environment Setup & Runner
# Usage: 
#   ./scripts/run_local.sh          (Prepares local DB, Redis, and runs migrations)
#   ./scripts/run_local.sh --start  (Runs local backend server in foreground)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

cd "${PROJECT_ROOT}"

echo "============================================================"
echo " Preparing ProspectOS for Local Development..."
echo "============================================================"

# 1. Ensure DB & Redis are running in Docker without port conflicts
echo "[1/4] Ensuring PostgreSQL and Redis are active..."
docker compose up -d db redis

# Stop dockerized application services so host ports 8000 and 3001 are free for local processes
if docker compose ps | grep -q "prospectos_backend"; then
    echo "Stopping containerized backend/worker/frontend to free ports for local run..."
    docker compose stop backend worker frontend > /dev/null 2>&1 || true
fi

# 2. Run Database Migrations locally
echo "[2/4] Applying Alembic database migrations..."
cd "${BACKEND_DIR}"
PYTHONPATH=. .venv/bin/alembic upgrade head

# 3. Generate / verify auth user
echo "[3/4] Checking Master Admin User & Authentication..."
cd "${PROJECT_ROOT}"
backend/.venv/bin/python scripts/get_auth.py

echo "[4/4] Local environment is ready!"
echo "============================================================"
echo " To run services locally in separate terminal tabs:"
echo "------------------------------------------------------------"
echo " 1. Backend API (FastAPI):"
echo "    cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000"
echo ""
echo " 2. Background Worker (ARQ):"
echo "    ./scripts/start_worker.sh --daemon   (or foreground: ./scripts/start_worker.sh)"
echo ""
echo " 3. Frontend UI (Next.js):"
echo "    cd frontend && npm run dev"
echo "    (Available at: http://localhost:3000 or http://localhost:3001)"
echo "============================================================"

ACTION="${1:-}"
if [ "${ACTION}" = "--start" ] || [ "${ACTION}" = "start" ]; then
    echo "Starting local FastAPI backend on http://localhost:8000..."
    cd "${BACKEND_DIR}"
    exec .venv/bin/uvicorn app.main:app --reload --port 8000
fi
