#!/bin/bash

# SMP Event Orchestrator - Startup Script
# This script starts the web application and event handler

echo "=========================================="
echo "SMP Event Orchestrator - Starting Up"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your configuration."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p database
mkdir -p events/events_json

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "gunicorn.*app:app" 2>/dev/null
pkill -f "event_handler.py" 2>/dev/null
sleep 2

# Start the event handler first
echo "🚀 Starting event handler..."
python3 src/event_handler.py > /dev/null 2>&1 &
EVENT_HANDLER_PID=$!

# Wait a moment for event handler to initialize
sleep 3

# Check if event handler is running
if pgrep -f "event_handler.py" > /dev/null; then
    echo "✅ Event handler started successfully (PID: $EVENT_HANDLER_PID)"
else
    echo "⚠️  Event handler may not have started properly"
fi

# Start gunicorn
echo "🌐 Starting web application with gunicorn..."
gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --timeout 120 \
    --daemon \
    --pid /tmp/gunicorn.pid \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log \
    app:app

# Wait for gunicorn to start
sleep 2

# Check if gunicorn is running
if [ -f /tmp/gunicorn.pid ]; then
    GUNICORN_PID=$(cat /tmp/gunicorn.pid)
    if ps -p $GUNICORN_PID > /dev/null; then
        echo "✅ Gunicorn started successfully (PID: $GUNICORN_PID)"
    else
        echo "❌ Gunicorn failed to start"
        exit 1
    fi
else
    echo "❌ Gunicorn PID file not found"
    exit 1
fi

echo ""
echo "=========================================="
echo "✨ SMP Event Orchestrator is running!"
echo "=========================================="
echo "📍 Web Interface: http://localhost:8080"
echo "📊 Event Handler: Running (PID: $EVENT_HANDLER_PID)"
echo "🌐 Gunicorn: Running (PID: $GUNICORN_PID)"
echo ""
echo "To stop the application, run: ./stop.sh"
echo "To view logs, run: tail -f logs/gunicorn-error.log"
echo "=========================================="
