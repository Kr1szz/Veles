#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PID_FILE="$PROJECT_ROOT/veles_server.pid"
LOG_FILE="$PROJECT_ROOT/veles_server.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Veles Shield is already running with PID $PID on port 8000."
        echo "Health check: $(curl -s http://localhost:8000/health || echo 'Starting up...')"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Ensure Redis is running
if [ -x "$PROJECT_ROOT/bin/redis-server" ] && ! "$PROJECT_ROOT/bin/redis-cli" ping &>/dev/null; then
    echo "Starting Redis daemon on port 6379..."
    "$PROJECT_ROOT/bin/redis-server" "$PROJECT_ROOT/redis.conf"
    sleep 0.5
fi

# Ensure C++ library is built
if [ ! -f "$PROJECT_ROOT/backend/cpp/libveles.so" ]; then
    echo "Compiling optional native C++ scoring library..."
    make -C backend/cpp
fi

echo "Starting Veles Shield API Gateway daemon in background..."
setsid "$PROJECT_ROOT/.venv/bin/python3" -m uvicorn aegis.main:app \
    --app-dir backend \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 2 \
    > "$LOG_FILE" 2>&1 < /dev/null &

PID=$!
echo $PID > "$PID_FILE"
echo "Veles Shield started with PID $PID. Logs: $LOG_FILE"

# Wait and verify health check
for i in {1..10}; do
    if curl -s http://localhost:8000/health | grep -q "HEALTHY"; then
        echo "=================================================================="
        echo "Veles Shield is LIVE & HEALTHY at http://localhost:8000"
        echo "- Dashboard:       http://localhost:8000"
        echo "- API Docs:        http://localhost:8000/docs"
        echo "- Health Probe:    http://localhost:8000/health"
        echo "=================================================================="
        exit 0
    fi
    sleep 0.5
done

echo "Warning: Server started (PID $PID), but health check did not respond yet. Check $LOG_FILE"
