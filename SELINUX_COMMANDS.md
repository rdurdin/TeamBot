# SELinux Commands for TeamAgent Web

Since SELinux management requires sudo/root access, you'll need to run these commands manually.

## Quick Setup (Recommended)

Run the automated setup script:

```bash
cd web
sudo ./setup-firewall-selinux.sh
```

This will configure everything automatically.

## Manual SELinux Configuration

If you prefer to run commands manually:

### 1. Add Port 3000 to SELinux

```bash
sudo semanage port -a -t http_port_t -p tcp 3000
```

If port already exists, modify it instead:

```bash
sudo semanage port -m -t http_port_t -p tcp 3000
```

### 2. Add Port 8000 to SELinux

```bash
sudo semanage port -a -t http_port_t -p tcp 8000
```

Or modify if exists:

```bash
sudo semanage port -m -t http_port_t -p tcp 8000
```

### 3. Verify SELinux Configuration

```bash
sudo semanage port -l | grep http_port_t
```

You should see ports 3000 and 8000 listed.

## Alternative: SELinux Booleans

If you're running the web server through Node.js/Python and not httpd, you may need:

```bash
# Allow httpd to make network connections
sudo setsebool -P httpd_can_network_connect 1

# Allow httpd to connect to network databases
sudo setsebool -P httpd_can_network_connect_db 1
```

## Troubleshooting SELinux Issues

### Check if SELinux is blocking

```bash
sudo ausearch -m avc -ts recent | grep -E "3000|8000"
```

### View SELinux denials

```bash
sudo tail -f /var/log/audit/audit.log | grep denied
```

### Temporarily set SELinux to permissive (NOT RECOMMENDED for production)

```bash
# Check current mode
getenforce

# Set to permissive temporarily (resets on reboot)
sudo setenforce 0

# Set back to enforcing
sudo setenforce 1
```

### Generate custom SELinux policy from denials

If you're still getting blocked:

```bash
# Install policycoreutils-python-utils if not installed
sudo dnf install policycoreutils-python-utils

# Generate policy from recent denials
sudo ausearch -m avc -ts recent | audit2allow -M teamagent_web

# Load the policy
sudo semodule -i teamagent_web.pp
```

## What's Already Done

✅ **Firewall**: Ports 3000 and 8000 are open
✅ **httpd**: Service is enabled and running
⚠️  **SELinux**: Needs sudo to configure (run setup script above)

## Why SELinux Matters

SELinux prevents processes from binding to ports that aren't explicitly allowed. Even though the firewall allows traffic on ports 3000 and 8000, SELinux will block Node.js (Vite) and Python (FastAPI) from listening on these ports unless configured.

### Symptoms of SELinux blocking:

- Vite dev server fails to start with "EACCES" or "permission denied"
- FastAPI/uvicorn can't bind to port 8000
- Process crashes with "Address already in use" even though nothing is using it

### Solution:

Add the ports to `http_port_t` context (commands above).

## Production Deployment

For production with httpd reverse proxy:

1. **Option A: Use standard ports**
   - Run Vite on 3000 internally (SELinux already allows)
   - Run FastAPI on 8000 internally (SELinux already allows)
   - Use httpd on port 80/443 externally (standard, no SELinux changes needed)

2. **Option B: Direct port binding**
   - Add custom ports to SELinux as shown above
   - More complex but gives you full control

## Verification

After running the commands, verify everything works:

```bash
# Check SELinux allows the ports
sudo semanage port -l | grep -E "3000|8000"

# Test binding to port 3000
python3 -m http.server 3000
# If no permission error, SELinux is configured correctly

# Test binding to port 8000
python3 -m http.server 8000
# If no permission error, SELinux is configured correctly
```

---

**Next Steps:**

1. Run: `sudo ./setup-firewall-selinux.sh`
2. Or run the manual SELinux commands above
3. Start the web UI: `./start.sh`
4. Access: http://localhost:3000
