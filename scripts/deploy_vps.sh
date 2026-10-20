#!/usr/bin/env bash
# ==============================================================================
# ProspectOS: Remote Linux VPS Automated Deployer
# Usage:
#   ./scripts/deploy_vps.sh --host <VPS_IP> [--user <SSH_USER>] [--port <SSH_PORT>] [--key <SSH_KEY>] [--domain <DOMAIN>]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

VPS_HOST=""
VPS_USER="root"
VPS_PORT="22"
SSH_KEY=""
DOMAIN=""
REMOTE_DIR="/opt/prospectos"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --host|-h)
      VPS_HOST="$2"
      shift 2
      ;;
    --user|-u)
      VPS_USER="$2"
      shift 2
      ;;
    --port|-p)
      VPS_PORT="$2"
      shift 2
      ;;
    --key|-i)
      SSH_KEY="$2"
      shift 2
      ;;
    --domain|-d)
      DOMAIN="$2"
      shift 2
      ;;
    --dir)
      REMOTE_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 --host <VPS_IP> [--user <SSH_USER>] [--port <SSH_PORT>] [--key <SSH_KEY>] [--domain <DOMAIN>]"
      exit 1
      ;;
  esac
done

if [ -z "${VPS_HOST}" ]; then
  echo "Error: --host <VPS_IP_OR_DOMAIN> is required."
  echo "Usage: $0 --host <VPS_IP> [--user root] [--port 22] [--key ~/.ssh/id_rsa]"
  exit 1
fi

SSH_OPTS=("-p" "${VPS_PORT}" "-o" "StrictHostKeyChecking=accept-new" "-o" "ConnectTimeout=10")
if [ -n "${SSH_KEY}" ]; then
  SSH_OPTS+=("-i" "${SSH_KEY}")
fi

echo "============================================================"
echo " ProspectOS: Remote VPS Deployment Initiated"
echo " Target Host:   ${VPS_USER}@${VPS_HOST}:${VPS_PORT}"
echo " Remote Path:   ${REMOTE_DIR}"
echo " Domain:        ${DOMAIN:-'Direct IP / HTTP'}"
echo "============================================================"

# Step 1: Check SSH Connectivity
echo "[1/6] Testing SSH connectivity to remote host..."
if ! ssh "${SSH_OPTS[@]}" "${VPS_USER}@${VPS_HOST}" "echo 'SSH Connection successful'" ; then
  echo "Error: Unable to connect via SSH to ${VPS_USER}@${VPS_HOST} on port ${VPS_PORT}."
  echo "Please verify that the IP, username, and SSH key/credentials are correct."
  exit 1
fi

# Step 2: Ensure Docker & Docker Compose are installed on remote host
echo "[2/6] Verifying remote Docker installation..."
ssh "${SSH_OPTS[@]}" "${VPS_USER}@${VPS_HOST}" bash -s << 'EOF'
set -euo pipefail
if ! command -v docker &> /dev/null; then
  echo "Docker not detected. Installing Docker via official get.docker.com..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

if ! docker compose version &> /dev/null; then
  echo "Installing Docker Compose plugin..."
  apt-get update -y && apt-get install -y docker-compose-plugin || true
fi

echo "Docker version: $(docker --version)"
echo "Docker compose version: $(docker compose version)"
EOF

# Step 3: Prepare remote directory and rsync project files
echo "[3/6] Syncing project files to ${REMOTE_DIR} on remote host..."
ssh "${SSH_OPTS[@]}" "${VPS_USER}@${VPS_HOST}" "mkdir -p ${REMOTE_DIR}/backups/ssl"

# Use rsync to sync codebase excluding local virtualenv, node_modules, and cache
RSYNC_SSH="ssh -p ${VPS_PORT}"
if [ -n "${SSH_KEY}" ]; then
  RSYNC_SSH="${RSYNC_SSH} -i ${SSH_KEY}"
fi

rsync -avz --delete \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='backend/.venv' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/.next' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='backups/*.dump' \
  -e "${RSYNC_SSH}" \
  "${PROJECT_ROOT}/" \
  "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/"

# Step 4: Ensure production environment file (.env) exists on remote
echo "[4/6] Configuring production environment on remote host..."
ssh "${SSH_OPTS[@]}" "${VPS_USER}@${VPS_HOST}" bash -s << EOF
set -euo pipefail
cd ${REMOTE_DIR}

if [ ! -f "backend/.env" ]; then
  echo "Generating secure production backend/.env..."
  POSTGRES_PASS=\$(openssl rand -hex 16)
  REDIS_PASS=\$(openssl rand -hex 16)
  SECRET_KEY=\$(openssl rand -hex 32)
  TOKEN_ENCRYPTION_KEY=\$(python3 -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())" 2>/dev/null || openssl rand -base64 32)

  cat > backend/.env << ENV_FILE
ENVIRONMENT=production
POSTGRES_USER=prospectos_user
POSTGRES_PASSWORD=\${POSTGRES_PASS}
POSTGRES_DB=prospectos
DATABASE_URL=postgresql+asyncpg://prospectos_user:\${POSTGRES_PASS}@db:5432/prospectos
REDIS_URL=redis://redis:6379/0
SECRET_KEY=\${SECRET_KEY}
TOKEN_ENCRYPTION_KEY=\${TOKEN_ENCRYPTION_KEY}
EMAIL_PROVIDER=none
LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-sonnet-5-5
ENV_FILE
fi

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
  cp .env.example .env
fi

# Set permissions
chmod 600 backend/.env 2>/dev/null || true
EOF

# Step 5: Build and Start Production Docker Stack
echo "[5/6] Building and starting production Docker containers on remote host..."
ssh "${SSH_OPTS[@]}" "${VPS_USER}@${VPS_HOST}" bash -s << EOF
set -euo pipefail
cd ${REMOTE_DIR}

echo "Stopping any existing containers..."
docker compose -f docker-compose.prod.yml down --remove-orphans || true

echo "Building and launching production stack..."
docker compose -f docker-compose.prod.yml up -d --build

echo "Waiting for services to become healthy..."
sleep 10
docker compose -f docker-compose.prod.yml ps
EOF

# Step 6: Verify Deployment and Run Health Check
echo "[6/6] Verifying remote deployment health..."
ssh "${SSH_OPTS[@]}" "${VPS_USER}@${VPS_HOST}" bash -s << 'EOF'
set -euo pipefail
cd /opt/prospectos

echo "Testing backend health via internal Nginx reverse proxy..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "FAILED")

if [ "$HEALTH_STATUS" = "200" ]; then
  echo "✓ Health Check: PASSED (HTTP 200 OK)"
else
  echo "⚠ Health Check returned: $HEALTH_STATUS. Inspecting logs..."
  docker compose -f docker-compose.prod.yml logs --tail=50 backend
fi
EOF

echo ""
echo "============================================================"
echo " ProspectOS: Remote VPS Deployment Finished!"
echo "============================================================"
echo " Access URL: http://${VPS_HOST}"
if [ -n "${DOMAIN}" ]; then
  echo " Domain URL: http://${DOMAIN}"
fi
echo " API Docs:   http://${VPS_HOST}/docs"
echo " Health:     http://${VPS_HOST}/health"
echo "============================================================"
