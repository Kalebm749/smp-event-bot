#!/bin/bash
cd ~/smp-event-bot
source venv/bin/activate

# Kill any existing gunicorn processes
pkill -f "gunicorn.*app:app"

# Start gunicorn
gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --timeout 120 \
    --daemon \
    --pid /tmp/gunicorn.pid \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log \
    app:app

echo "Gunicorn started with PID: $(cat /tmp/gunicorn.pid)"
