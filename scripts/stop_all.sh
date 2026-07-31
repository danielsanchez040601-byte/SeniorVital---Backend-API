#!/bin/bash
LOG_DIR="$(cd "$(dirname "$0")/.." && pwd)/logs"
if [ -d "$LOG_DIR" ]; then
    for pid_file in "$LOG_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            NAME=$(basename "$pid_file" .pid)
            PID=$(cat "$pid_file")
            echo "Stopping $NAME (PID: $PID)"
            kill "$PID" 2>/dev/null || true
            rm "$pid_file"
        fi
    done
fi
# Kill any remaining uvicorn on our ports
for port in 8000 8001 8002 8003 8004 8005 8006; do
    pid=$(netstat -ano 2>/dev/null | grep ":$port " | awk '{print $NF}' | sort -u)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
    fi
done
echo "All services stopped."
