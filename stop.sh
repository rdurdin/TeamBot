#!/bin/bash

# TeamAgent Web UI Stop Script

echo "🛑 Stopping TeamAgent Web UI..."

# Read PIDs if they exist
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✓ Backend stopped (PID: $BACKEND_PID)" || echo "⚠ Backend not running"
    rm -f .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✓ Frontend stopped (PID: $FRONTEND_PID)" || echo "⚠ Frontend not running"
    rm -f .frontend.pid
fi

# Fallback: kill by port
if lsof -ti:8000 > /dev/null 2>&1; then
    kill $(lsof -ti:8000) 2>/dev/null && echo "✓ Killed process on port 8000"
fi

if lsof -ti:3000 > /dev/null 2>&1; then
    kill $(lsof -ti:3000) 2>/dev/null && echo "✓ Killed process on port 3000"
fi

echo "✓ All servers stopped"
