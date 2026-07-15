#!/bin/bash

# TeamAgent Multi-VM Collaboration Setup Script

echo "🤖 TeamAgent Multi-VM Collaboration Setup"
echo "=========================================="
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "✓ Server IP detected: $SERVER_IP"
echo ""

# Configure firewall
echo "📡 Configuring firewall..."
echo "   Opening ports 3000 (frontend) and 8000 (backend)..."
echo ""
echo "Run these commands:"
echo ""
echo "  sudo firewall-cmd --permanent --add-port=3000/tcp"
echo "  sudo firewall-cmd --permanent --add-port=8000/tcp"
echo "  sudo firewall-cmd --reload"
echo ""
read -p "Press Enter after running the above commands..."

# Verify firewall
echo ""
echo "Verifying firewall configuration..."
sudo firewall-cmd --list-ports | grep -q "3000/tcp" && echo "✓ Port 3000 open" || echo "❌ Port 3000 not open"
sudo firewall-cmd --list-ports | grep -q "8000/tcp" && echo "✓ Port 8000 open" || echo "❌ Port 8000 not open"
echo ""

# Check if servers are running
echo "Checking if TeamAgent is running..."
if curl -s http://localhost:8000/ | grep -q "TeamAgent API"; then
    echo "✓ Backend running on port 8000"
else
    echo "❌ Backend not running - run ./start.sh"
fi

if curl -s http://localhost:3000/ | grep -q "html"; then
    echo "✓ Frontend running on port 3000"
else
    echo "❌ Frontend not running - run ./start.sh"
fi
echo ""

# Test from remote
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "To access from other VMs, use:"
echo ""
echo "  http://$SERVER_IP:3000"
echo ""
echo "Test from another VM:"
echo "  curl http://$SERVER_IP:3000/"
echo ""
echo "Or open in browser on VM2/VM3:"
echo "  firefox http://$SERVER_IP:3000"
echo ""
