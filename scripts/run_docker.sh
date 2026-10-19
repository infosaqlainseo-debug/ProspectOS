#!/usr/bin/env bash
# ==============================================================================
# ProspectOS: Full Docker Stack Runner & Health Verifier
# Usage: ./scripts/run_docker.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "============================================================"
echo " Starting ProspectOS Full Stack on Docker..."
echo "============================================================"

docker compose up -d

echo ""
echo "Waiting for services to report healthy/ready..."
sleep 3

docker compose ps

echo ""
echo "============================================================"
echo " ProspectOS Service URLs & Endpoints"
echo "============================================================"
echo " • Frontend Web UI:     http://localhost:3001"
echo " • Backend API:         http://localhost:8000"
echo " • API Documentation:   http://localhost:8000/docs"
echo " • Health Check:        http://localhost:8000/health"
echo " • Database:            PostgreSQL 15 (localhost:5432)"
echo " • Queue / Cache:       Redis 7 (localhost:6379)"
echo " • Background Worker:   ARQ Worker (running in Docker)"
echo "============================================================"
echo ""
echo "Testing Backend Health..."
curl -s http://localhost:8000/health || echo "Backend not ready yet"
echo ""

echo "Getting Authentication Credentials..."
if [ -f "backend/.venv/bin/python" ]; then
    backend/.venv/bin/python scripts/get_auth.py
fi
