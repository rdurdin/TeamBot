#!/bin/bash

# TeamAgent Web - Firewall and SELinux Setup Script
# Run with: sudo ./setup-firewall-selinux.sh

set -e

echo "🔒 TeamAgent Web - Firewall & SELinux Configuration"
echo "===================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo ./setup-firewall-selinux.sh"
    exit 1
fi

# 1. Firewall Configuration
echo "📡 Configuring firewall..."
echo "  Adding port 3000/tcp (Frontend)..."
firewall-cmd --add-port=3000/tcp --permanent

echo "  Adding port 8000/tcp (Backend API)..."
firewall-cmd --add-port=8000/tcp --permanent

echo "  Adding HTTP service..."
firewall-cmd --add-service=http --permanent

echo "  Adding HTTPS service..."
firewall-cmd --add-service=https --permanent

echo "  Reloading firewall..."
firewall-cmd --reload

echo "✓ Firewall configured"
echo ""

# 2. HTTPD Service
echo "🌐 Configuring httpd service..."
systemctl enable httpd
systemctl start httpd
systemctl status httpd --no-pager | head -5

echo "✓ httpd service enabled and started"
echo ""

# 3. SELinux Configuration
echo "🔐 Configuring SELinux..."
SELINUX_MODE=$(getenforce)
echo "  Current SELinux mode: $SELINUX_MODE"

if [ "$SELINUX_MODE" == "Enforcing" ]; then
    echo "  Adding port 3000 to http_port_t..."
    semanage port -a -t http_port_t -p tcp 3000 2>/dev/null || \
    semanage port -m -t http_port_t -p tcp 3000

    echo "  Adding port 8000 to http_port_t..."
    semanage port -a -t http_port_t -p tcp 8000 2>/dev/null || \
    semanage port -m -t http_port_t -p tcp 8000

    echo "  Verifying SELinux port configuration..."
    semanage port -l | grep -E "3000|8000"

    echo "✓ SELinux configured for ports 3000 and 8000"
else
    echo "⚠ SELinux is in $SELINUX_MODE mode - skipping port configuration"
fi
echo ""

# 4. Verify Configuration
echo "📋 Configuration Summary:"
echo "========================"
echo ""
echo "Firewall ports:"
firewall-cmd --list-ports
echo ""
echo "Firewall services:"
firewall-cmd --list-services
echo ""
echo "httpd status:"
systemctl is-active httpd && echo "  ✓ Active" || echo "  ✗ Inactive"
systemctl is-enabled httpd && echo "  ✓ Enabled" || echo "  ✗ Disabled"
echo ""

if [ "$SELINUX_MODE" == "Enforcing" ]; then
    echo "SELinux http ports:"
    semanage port -l | grep http_port_t | grep -E "3000|8000" || echo "  (custom ports not shown)"
fi

echo ""
echo "===================================================="
echo "✅ Configuration Complete!"
echo ""
echo "You can now:"
echo "  1. Start backend:  cd backend && python api.py"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Access at:      http://localhost:3000"
echo ""
echo "Or use the convenience script:"
echo "  ./start.sh"
echo ""
