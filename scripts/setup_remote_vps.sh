#!/usr/bin/env bash
# ==============================================================================
# ProspectOS: Standalone Remote VPS Setup & Launcher Script
# Run this directly on your remote Ubuntu/Debian VPS:
#   curl -sSL https://raw.githubusercontent.com/.../setup_remote_vps.sh | bash
#   or: sudo bash scripts/setup_remote_vps.sh
# ==============================================================================

set -euo pipefail

echo "============================================================"
echo " ProspectOS: Standalone Remote VPS Installation & Launcher"
echo "============================================================"

# Ensure running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or using sudo: sudo bash $0"
  exit 1
fi

INSTALL_DIR="/opt/prospectos"
REPO_URL="https://github.com/infosaqlainseo-debug/ProspectOS.git"

# Step 1: Install prerequisite packages & Docker
echo "[1/6] Installing prerequisites and Docker..."
apt-get update -y
apt-get install -y curl git rsync openssl ufw

if ! command -v docker &> /dev/null; then
  echo "Installing Docker engine..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

if ! docker compose version &> /dev/null; then
  echo "Installing Docker Compose plugin..."
  apt-get install -y docker-compose-plugin || true
fi

# Step 2: Configure Firewall (UFW)
echo "[2/6] Configuring UFW firewall rules..."
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP (Nginx)"
ufw allow 443/tcp comment "HTTPS (Nginx)"
# Explicitly ensure internal database ports are not exposed
ufw deny 5432/tcp comment "Deny public Postgres" || true
ufw deny 6379/tcp comment "Deny public Redis" || true
echo "y" | ufw enable || true

# Step 3: Clone or update repository
echo "[3/6] Setting up application in ${INSTALL_DIR}..."
if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "Updating existing repository in ${INSTALL_DIR}..."
  cd "${INSTALL_DIR}"
  git fetch origin
  git checkout main
  git pull origin main
else
  echo "Cloning repository into ${INSTALL_DIR}..."
  mkdir -p "$(dirname "${INSTALL_DIR}")"
  git clone "${REPO_URL}" "${INSTALL_DIR}"
  cd "${INSTALL_DIR}"
fi

# Step 4: Ensure production environment and SSL folders
echo "[4/6] Setting up production environment..."
mkdir -p "${INSTALL_DIR}/backups/ssl"

if [ ! -f "${INSTALL_DIR}/backend/.env" ]; then
  echo "Generating secure production backend/.env..."
  POSTGRES_PASS=$(openssl rand -hex 16)
  SECRET_KEY=$(openssl rand -hex 32)
  TOKEN_ENCRYPTION_KEY=$(openssl rand -base64 32)

  cat > "${INSTALL_DIR}/backend/.env" << ENV_FILE
ENVIRONMENT=production
POSTGRES_USER=prospectos_user
POSTGRES_PASSWORD=${POSTGRES_PASS}
POSTGRES_DB=prospectos
DATABASE_URL=postgresql+asyncpg://prospectos_user:${POSTGRES_PASS}@db:5432/prospectos
REDIS_URL=redis://redis:6379/0
SECRET_KEY=${SECRET_KEY}
TOKEN_ENCRYPTION_KEY=${TOKEN_ENCRYPTION_KEY}
EMAIL_PROVIDER=none
LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-sonnet-5-5
ENV_FILE
  chmod 600 "${INSTALL_DIR}/backend/.env"
fi

# Step 5: Launch Production Containers
echo "[5/6] Building and starting production Docker stack..."
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --build

# Step 6: Verify Health
echo "[6/6] Verifying service health..."
sleep 15
docker compose -f docker-compose.prod.yml ps

SERVER_IP=$(curl -s -4 ifconfig.me || hostname -I | awk '{print $1}')

echo ""
echo "============================================================"
echo " ProspectOS: Remote VPS Deployment Successful!"
echo "============================================================"
echo " • Web Dashboard:  http://${SERVER_IP}"
echo " • API Docs:       http://${SERVER_IP}/docs"
echo " • Health Check:   http://${SERVER_IP}/health"
echo "============================================================"
