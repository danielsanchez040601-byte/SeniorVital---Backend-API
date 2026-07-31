#!/bin/bash
# Windows-compatible start script (works in Git Bash / WSL)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
mkdir -p "$ROOT_DIR/storage/videos" "$ROOT_DIR/storage/progress-photos"

start_service() {
    NAME=$1
    PORT=$2
    DIR=$3
    PID_FILE="$LOG_DIR/$NAME.pid"
    LOG_FILE="$LOG_DIR/$NAME.log"
    cd "$DIR"
    PYTHONPATH="$ROOT_DIR" python -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started $NAME on port $PORT (PID: $!)"
    sleep 3
}

start_service "auth-profile" 8001 "$ROOT_DIR/auth-profile-service"
start_service "catalog" 8002 "$ROOT_DIR/catalog-service"
start_service "routines-ai" 8003 "$ROOT_DIR/routines-ai-service"
start_service "tracking" 8004 "$ROOT_DIR/tracking-service"
start_service "dashboard" 8005 "$ROOT_DIR/dashboard-service"
start_service "notification" 8006 "$ROOT_DIR/notification-service"
start_service "gateway" 8000 "$ROOT_DIR/gateway"

echo ""
echo "All services started. PIDs in $LOG_DIR"
