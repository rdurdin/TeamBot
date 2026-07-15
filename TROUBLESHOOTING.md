# Troubleshooting: Website Hanging

## Issue: Frontend hanging/not loading

If the website hangs when you open http://localhost:3000, try these steps:

### Step 1: Kill all processes and restart fresh

```bash
# Kill everything
pkill -9 -f "python.*api.py"
pkill -9 -f "vite"
pkill -9 -f "npm.*dev"

# Wait a moment
sleep 2
```

### Step 2: Start Backend First

```bash
cd /home/ybounkib/intern_project/TeamAgent/web/backend
source venv/bin/activate
python api.py
```

**Keep this terminal open!** You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Frontend in NEW Terminal

Open a **new terminal window** and run:

```bash
cd /home/ybounkib/intern_project/TeamAgent/web/frontend
npm run dev
```

**Keep this terminal open too!** You should see:
```
VITE v5.x.x ready in xxx ms
➜  Local:   http://localhost:3000/
```

### Step 4: Open Browser

Open http://localhost:3000

**Wait 5-10 seconds** for the engineers to be created on first load.

## Common Issues

### Issue: "Hanging on blank screen"

**Cause:** Frontend is trying to create engineers but API call is slow or failing

**Fix:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for error messages
4. Check Network tab for failed requests

### Issue: "CORS errors"

**Symptom:** Console shows "CORS policy blocked"

**Fix:** This shouldn't happen with the proxy, but if it does:
1. Make sure backend is running on port 8000
2. Make sure you're accessing via http://localhost:3000 (not 127.0.0.1)
3. Restart both servers

### Issue: "WebSocket connection failed"

**Symptom:** Live feed not updating

**Fix:**
1. Check backend logs for WebSocket errors
2. Make sure firewall allows port 8000
3. Try refreshing the page

### Issue: "Terminal not rendering"

**Symptom:** Blank boxes where terminals should be

**Fix:**
1. Check browser console for xterm errors
2. Clear browser cache (Ctrl+Shift+R)
3. Try different browser (Chrome works best)

## Debug Steps

### Check if backend is responding:
```bash
curl http://localhost:8000/
```
Should return: `{"service":"TeamAgent API", ...}`

### Check if frontend is responding:
```bash
curl http://localhost:3000/
```
Should return HTML

### Check if proxy works:
```bash
curl http://localhost:3000/api/
```
Should return: `{"service":"TeamAgent API", ...}`

### Check browser console:
1. Open DevTools (F12)
2. Console tab - look for JavaScript errors
3. Network tab - look for failed requests (red)
4. Look for any error about engineers, API, or WebSocket

## Manual Fix: Create Engineers Beforehand

If the frontend keeps hanging on engineer creation, create them manually:

```bash
# Create Alice
curl -X POST http://localhost:8000/engineers/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice (Engineer A)","email":"alice@teamagent.demo","git_username":"alice"}'

# Create Bob
curl -X POST http://localhost:8000/engineers/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob (Engineer B)","email":"bob@teamagent.demo","git_username":"bob"}'
```

Then the frontend should load faster.

## Nuclear Option: Complete Reset

If nothing works:

```bash
# Kill everything
pkill -9 -f "python.*api"
pkill -9 -f "vite"
pkill -9 -f "npm"

# Clear node_modules and reinstall
cd /home/ybounkib/intern_project/TeamAgent/web/frontend
rm -rf node_modules package-lock.json
npm install

# Clear Python cache
cd /home/ybounkib/intern_project/TeamAgent/web/backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Restart both
cd /home/ybounkib/intern_project/TeamAgent/web/backend
source venv/bin/activate
python api.py

# In new terminal:
cd /home/ybounkib/intern_project/TeamAgent/web/frontend
npm run dev
```

## Check Logs

### Backend logs:
```bash
# If started with nohup
cat /tmp/backend_test.log

# If running in terminal, check that terminal
```

### Frontend logs:
Look at the terminal where you ran `npm run dev`

## Still Hanging?

The issue might be:

1. **Slow API responses** - Backend taking too long
2. **Network issues** - Firewall blocking localhost
3. **Browser issues** - Try incognito mode
4. **React hydration** - Frontend React app not initializing

**Quick test:**
```bash
# Test backend speed
time curl http://localhost:8000/

# Should be < 100ms
```

If backend is slow, there might be database issues.

## Alternative: Use Simple HTML Version

If the React app keeps hanging, I can create a simple HTML version without React that will definitely work.

Let me know what errors you see in the browser console!
