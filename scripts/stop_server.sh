#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_ROOT/veles_server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Veles Shield (PID $PID)..."
        kill "$PID" 2>/dev/null || true
        # Also kill any remaining uvicorn workers
        pkill -P "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
        echo "Veles Shield stopped successfully."
        exit 0
    else
        echo "PID file exists but process $PID is not running. Cleaning up..."
        rm -f "$PID_FILE"
    fi
else
    # Fallback check
    PIDS=$(pgrep -f "uvicorn aegis.main:app" || true)
    if [ -n "$PIDS" ]; then
        echo "Stopping uvicorn processes: $PIDS"
        kill $PIDS 2>/dev/null || true
        echo "Stopped."
        exit 0
    fi
    echo "Veles Shield is not running."
fi
