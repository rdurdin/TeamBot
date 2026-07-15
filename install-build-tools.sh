#!/bin/bash

# Install build tools needed for Python packages with native extensions

echo "📦 Installing build tools for Python..."
echo ""

# Install GCC and development tools
echo "Installing GCC and development tools..."
sudo dnf groupinstall -y "Development Tools"

# Install Python development headers
echo "Installing Python development headers..."
sudo dnf install -y python3-devel

# Install Rust (needed for pydantic-core)
echo "Installing Rust (needed for pydantic-core)..."
sudo dnf install -y rust cargo

echo ""
echo "✓ Build tools installation complete!"
echo ""
echo "Now run: ./start.sh"
