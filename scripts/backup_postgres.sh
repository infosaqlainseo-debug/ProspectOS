#!/usr/bin/env bash
# ==============================================================================
# ProspectOS: Automated Daily PostgreSQL Backup Script
# Usage: ./scripts/backup_postgres.sh
# Can be scheduled via crontab: 0 2 * * * /path/to/ProspectOS/scripts/backup_postgres.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backend/backups"
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting automated database backup..." >> "${LOG_FILE}"

cd "${PROJECT_ROOT}/backend"

if [ -f ".venv/bin/python" ]; then
    PYTHONPATH=. .venv/bin/python scripts/backup_manager.py --backup >> "${LOG_FILE}" 2>&1
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup execution completed via backup_manager.py." >> "${LOG_FILE}"
else
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Python virtual environment not found. Falling back to direct container pg_dump..." >> "${LOG_FILE}"
    TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
    DUMP_FILE="${BACKUP_DIR}/prospectos_backup_${TIMESTAMP}.dump"
    docker exec prospectos_db pg_dump -U user -d prospectos -F c -b > "${DUMP_FILE}"
    chmod 600 "${DUMP_FILE}"
    shasum -a 256 "${DUMP_FILE}" > "${DUMP_FILE}.sha256"
    chmod 600 "${DUMP_FILE}.sha256"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Direct backup completed: ${DUMP_FILE}" >> "${LOG_FILE}"
fi
