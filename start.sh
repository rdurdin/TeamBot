#!/bin/bash

# TeamAgent Web UI Startup Script

set -e

echo "🤖 TeamAgent Web UI Startup"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the web directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from the web/ directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm not found. Please install Node.js 16+"
    exit 1
fi

echo "✓ Python 3: $(python3 --version)"
echo "✓ npm: $(npm --version)"
echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Python 3.14 compatibility fix for pydantic-core
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

pip install -q -r requirements.txt
echo "✓ Backend dependencies installed"
cd ..
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Running npm install..."
    npm install --silent
else
    echo "✓ node_modules exists, skipping npm install"
fi
echo "✓ Frontend dependencies installed"
cd ..
echo ""

# Start backend in background
echo "🚀 Starting backend server..."
cd backend
source venv/bin/activate
python api.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID) on http://localhost:8000"
cd ..
echo ""

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "❌ Backend failed to start. Check backend/backend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo "✓ Backend is ready"
echo ""

# Start frontend
echo "🚀 Starting frontend dev server..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID) on http://localhost:3000"
cd ..
echo ""

# Save PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "=============================="
echo -e "${GREEN}✓ TeamAgent Web UI is running!${NC}"
echo "=============================="
echo ""
echo -e "🌐 Open your browser to: ${BLUE}http://localhost:3000${NC}"
echo ""
echo "📊 Monitor logs:"
echo "  - Backend:  tail -f web/backend.log"
echo "  - Frontend: tail -f web/frontend.log"
echo ""
echo "🛑 To stop the servers:"
echo "  - Run: ./stop.sh"
echo "  - Or press Ctrl+C and run: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; echo 'Servers stopped.'; exit 0" INT

# Keep script running
wait
