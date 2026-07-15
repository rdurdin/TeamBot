# Manual Installation Guide

If the automated `start.sh` script fails, follow these manual steps:

## Step 1: Install Backend Dependencies

```bash
cd /home/ybounkib/intern_project/TeamAgent/web/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Set compatibility flag for Python 3.14
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 2: Install Frontend Dependencies

```bash
cd /home/ybounkib/intern_project/TeamAgent/web/frontend

# Install npm packages
npm install
```

## Step 3: Start Backend Server

In one terminal:

```bash
cd /home/ybounkib/intern_project/TeamAgent/web/backend
source venv/bin/activate
python api.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

## Step 4: Start Frontend Server

In a **new terminal**:

```bash
cd /home/ybounkib/intern_project/TeamAgent/web/frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**Keep this terminal open too!**

## Step 5: Open in Browser

Open your browser to:
```
http://localhost:3000
```

You should see the TeamAgent terminal interface with two side-by-side terminals!

## Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:** Make sure you activated the venv:
```bash
source venv/bin/activate
```

### Frontend won't start

**Error:** `Cannot find module 'vite'`

**Fix:** Install dependencies:
```bash
cd frontend
npm install
```

### Port already in use

**Error:** `Address already in use`

**Fix:** Kill existing processes:
```bash
# Kill backend
lsof -ti:8000 | xargs kill -9

# Kill frontend  
lsof -ti:3000 | xargs kill -9
```

### Python 3.14 compatibility error

If you still get pydantic-core build errors, try this before `pip install`:

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install pydantic-core --no-cache-dir
pip install -r requirements.txt
```

Or use pre-built wheels (already configured in requirements.txt).

## Verification

Once both servers are running, verify:

1. **Backend health check:**
   ```bash
   curl http://localhost:8000/
   ```
   Should return: `{"service":"TeamAgent API","version":"1.0.0","status":"operational"}`

2. **Frontend accessible:**
   Open http://localhost:3000 in browser

3. **WebSocket working:**
   Type commands in the terminals - you should see live updates in the sidebar

## Demo Commands

Try these in the web interface:

**Terminal A:**
```
ask variable x equals 10
```

**Terminal B:**
```
search variable
```

You should see Terminal B instantly find Terminal A's question!

---

**Stuck?** Check the error logs and refer to TROUBLESHOOTING.md
