# How to Restart Servers After Updates

## Quick Restart

### Terminal 1 - Restart Backend
```bash
# Stop old backend
pkill -f "python.*api.py"

# Start new backend
cd /home/ybounkib/intern_project/TeamAgent/web/backend
source venv/bin/activate
python api.py
```

### Terminal 2 - Restart Frontend
```bash
# Stop old frontend (Ctrl+C in the terminal running it)
# Or: pkill -f "vite"

# Start new frontend
cd /home/ybounkib/intern_project/TeamAgent/web/frontend
npm run dev
```

Then refresh your browser at http://localhost:3000

## What's New

### AI Command Added!

You can now use:
```
ai <question>
```

**Example:**
```
ai What is variable x equals 10
```

**Note:** If AI API is not configured, you'll see a helpful error message explaining what environment variables to set.

### Updated Commands

| Command | Description |
|---------|-------------|
| `ask <question>` | Save question to team database |
| `ai <question>` | Get AI-powered answer (if configured) |
| `search <query>` | Search team knowledge base |
| `recent` | Show recent questions |
| `memory` | Show memory entries |
| `help` | Show available commands |
| `clear` | Clear terminal |

## To Enable AI

Set these environment variables before starting the backend:

```bash
export MODEL_API="https://your-claude-api-endpoint"
export USER_KEY="your-api-key"
export MODEL_ID="claude-sonnet-4-6"
```

Then start the backend:
```bash
cd /home/ybounkib/intern_project/TeamAgent/web/backend
source venv/bin/activate
python api.py
```

## Demonstration Without AI

Even without AI configured, you can still demonstrate:

1. **Collaborative Q&A:**
   - Terminal A: `ask variable x equals 10`
   - Terminal B: `search variable`
   - See instant results!

2. **Real-time Memory:**
   - Watch the sidebar update as you type commands
   - See all commands from both engineers

3. **Team Knowledge:**
   - Use `recent` to see all questions
   - Use `memory` to see command history

The system shows **collaboration and memory persistence**, which is the core value proposition!

## Current Functionality

✅ **Working Without AI:**
- Collaborative Q&A system
- Real-time command synchronization
- Searchable knowledge base
- Memory visualization
- Multi-engineer support

⚠️ **Requires AI Configuration:**
- Automatic AI responses to questions
- AI-powered search and suggestions

The system is valuable even without AI - it solves the problem of engineers losing context and having to re-explain things to each other!
