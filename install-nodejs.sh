#!/bin/bash

# Install Node.js on Fedora

echo "📦 Installing Node.js and npm..."
echo ""

# Method 1: Using dnf (Fedora package manager)
echo "Installing via dnf..."
sudo dnf install -y nodejs npm

echo ""
echo "Verifying installation..."
node --version
npm --version

echo ""
echo "✓ Node.js installation complete!"
echo ""
echo "Now run: ./start.sh"
