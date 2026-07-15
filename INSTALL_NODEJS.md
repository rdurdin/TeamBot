# Installing Node.js on Fedora

Node.js is required for the frontend development server (Vite).

## Quick Install (Recommended)

```bash
sudo dnf install -y nodejs npm
```

Then verify:
```bash
node --version  # Should show v16.x or higher
npm --version   # Should show 8.x or higher
```

## Alternative: Install Latest LTS via NodeSource

If you want the latest Node.js LTS version:

### Node.js 20.x (Latest LTS)
```bash
# Download and run NodeSource setup script
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -

# Install Node.js
sudo dnf install -y nodejs

# Verify
node --version
npm --version
```

### Node.js 18.x (Previous LTS)
```bash
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs
```

## Alternative: Using nvm (Node Version Manager)

For multiple Node.js versions:

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell
source ~/.bashrc

# Install Node.js 20 LTS
nvm install 20

# Use it
nvm use 20

# Set as default
nvm alias default 20

# Verify
node --version
npm --version
```

## After Installation

Once Node.js is installed, return to the web directory and run:

```bash
cd /home/ybounkib/intern_project/TeamAgent/web
./start.sh
```

The script will now succeed!

## Troubleshooting

### Command not found after install
Reload your shell:
```bash
source ~/.bashrc
# or
hash -r
```

### Permission issues with npm
Don't use sudo with npm install. If you get permission errors:
```bash
# Fix npm permissions
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Version too old
Fedora's default Node.js might be old. Use NodeSource (above) for latest version.

---

**Next Steps:**
1. Install Node.js: `sudo dnf install -y nodejs npm`
2. Run setup: `cd web && ./start.sh`
3. Access: http://localhost:3000
