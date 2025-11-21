#!/bin/bash

# SMP Event Orchestrator - Stop Script
# This script stops the web application and event handler

echo "=========================================="
echo "SMP Event Orchestrator - Shutting Down"
echo "=========================================="

# Stop gunicorn
echo "🛑 Stopping gunicorn..."
if [ -f /tmp/gunicorn.pid ]; then
    GUNICORN_PID=$(cat /tmp/gunicorn.pid)
    if ps -p $GUNICORN_PID > /dev/null; then
        kill $GUNICORN_PID
        echo "✅ Gunicorn stopped (PID: $GUNICORN_PID)"
    else
        echo "⚠️  Gunicorn process not found"
    fi
    rm -f /tmp/gunicorn.pid
else
    echo "⚠️  Gunicorn PID file not found"
    pkill -f "gunicorn.*app:app"
fi

# Stop event handler
echo "🛑 Stopping event handler..."
if pgrep -f "event_handler.py" > /dev/null; then
    pkill -f "event_handler.py"
    echo "✅ Event handler stopped"
else
    echo "⚠️  Event handler process not found"
fi

# Wait a moment for processes to stop
sleep 2

# Verify everything is stopped
GUNICORN_RUNNING=$(pgrep -f "gunicorn.*app:app" | wc -l)
HANDLER_RUNNING=$(pgrep -f "event_handler.py" | wc -l)

echo ""
echo "=========================================="
if [ $GUNICORN_RUNNING -eq 0 ] && [ $HANDLER_RUNNING -eq 0 ]; then
    echo "✅ All processes stopped successfully"
else
    echo "⚠️  Some processes may still be running:"
    [ $GUNICORN_RUNNING -gt 0 ] && echo "   - Gunicorn: $GUNICORN_RUNNING process(es)"
    [ $HANDLER_RUNNING -gt 0 ] && echo "   - Event Handler: $HANDLER_RUNNING process(es)"
    echo ""
    echo "You may need to manually kill these processes"
fi
echo "=========================================="
