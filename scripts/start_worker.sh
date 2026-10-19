#!/usr/bin/env bash
# ==============================================================================
# ProspectOS: Background ARQ Worker Lifecycle Manager
# Usage:
#   ./scripts/start_worker.sh          (Run in foreground)
#   ./scripts/start_worker.sh --daemon (Run in background with PID tracking)
#   ./scripts/start_worker.sh --status (Check worker process & health)
#   ./scripts/start_worker.sh --stop   (Gracefully terminate background worker)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
PID_FILE="${BACKEND_DIR}/arq_worker.pid"
LOG_FILE="${BACKEND_DIR}/arq.log"

cd "${BACKEND_DIR}"

check_redis() {
    if ! docker exec prospectos_redis redis-cli ping > /dev/null 2>&1; then
        echo "[ERROR] Redis is not reachable at localhost:6379." >&2
        echo "Please ensure the Redis container is running: docker compose up -d redis" >&2
        exit 1
    fi
}

get_worker_pid() {
    if [ -f "${PID_FILE}" ]; then
        local pid
        pid=$(cat "${PID_FILE}")
        if ps -p "${pid}" > /dev/null 2>&1; then
            echo "${pid}"
            return 0
        fi
    fi
    echo ""
}

ACTION="${1:---run}"

case "${ACTION}" in
    --status)
        PID=$(get_worker_pid)
        if [ -n "${PID}" ]; then
            echo "[STATUS] ARQ Worker is RUNNING (PID: ${PID})"
            PYTHONPATH=. .venv/bin/arq app.workers.worker.WorkerSettings --check || true
        else
            echo "[STATUS] ARQ Worker is NOT running."
            PYTHONPATH=. .venv/bin/arq app.workers.worker.WorkerSettings --check || true
        fi
        ;;

    --stop)
        PID=$(get_worker_pid)
        if [ -n "${PID}" ]; then
            echo "[SHUTDOWN] Stopping ARQ Worker (PID: ${PID})..."
            kill -TERM "${PID}"
            for i in {1..10}; do
                if ps -p "${PID}" > /dev/null 2>&1; then
                    sleep 1
                else
                    break
                fi
            done
            if ps -p "${PID}" > /dev/null 2>&1; then
                kill -KILL "${PID}"
            fi
            rm -f "${PID_FILE}"
            echo "[SHUTDOWN] Worker stopped."
        else
            echo "[INFO] No running ARQ Worker found."
            rm -f "${PID_FILE}"
        fi
        ;;

    --daemon)
        check_redis
        PID=$(get_worker_pid)
        if [ -n "${PID}" ]; then
            echo "[WARNING] ARQ Worker is already running (PID: ${PID})."
            exit 0
        fi
        echo "[START] Launching ARQ Worker in daemon mode..."
        nohup .venv/bin/arq app.workers.worker.WorkerSettings >> "${LOG_FILE}" 2>&1 &
        NEW_PID=$!
        echo "${NEW_PID}" > "${PID_FILE}"
        sleep 2
        if ps -p "${NEW_PID}" > /dev/null 2>&1; then
            echo "[START] ARQ Worker successfully started in background (PID: ${NEW_PID})."
            echo "Logs streaming to: ${LOG_FILE}"
        else
            echo "[ERROR] Failed to start ARQ Worker. Check ${LOG_FILE} for details."
            rm -f "${PID_FILE}"
            exit 1
        fi
        ;;

    --run|*)
        check_redis
        echo "[START] Running ARQ Worker in foreground..."
        exec .venv/bin/arq app.workers.worker.WorkerSettings
        ;;
esac
