#!/bin/bash

# Simple startup script for TeamAgent Web UI
# Opens two terminals (requires gnome-terminal or similar)

echo "🚀 Starting TeamAgent Web UI..."
echo ""

# Start backend in new terminal
gnome-terminal --title="TeamAgent Backend" -- bash -c "
cd /home/ybounkib/intern_project/TeamAgent/web/backend
source venv/bin/activate
echo '✓ Backend starting on http://localhost:8000'
python api.py
exec bash
" &

sleep 2

# Start frontend in new terminal
gnome-terminal --title="TeamAgent Frontend" -- bash -c "
cd /home/ybounkib/intern_project/TeamAgent/web/frontend
echo '✓ Frontend starting on http://localhost:3000'
npm run dev
exec bash
" &

sleep 3

echo "✓ Backend: http://localhost:8000"
echo "✓ Frontend: http://localhost:3000"
echo ""
echo "🌐 Opening browser..."
xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"
echo ""
echo "Press Ctrl+C in each terminal window to stop the servers"
