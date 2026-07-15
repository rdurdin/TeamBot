# TeamAgent Web UI

Interactive terminal-style web interface showcasing TeamAgent's collaborative memory and real-time Q&A features.

## Features

✨ **Split Terminal View** - Simulate two engineers working simultaneously
🧠 **Live Memory Feed** - Real-time visualization of all commands and interactions
📚 **Q&A Archive** - Searchable team knowledge base
🔄 **WebSocket Sync** - Instant updates across all terminals
🎨 **Terminal UI** - Authentic terminal experience with xterm.js

## Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (React + Vite)                    │
│  ├── Terminal A (xterm.js)                  │
│  ├── Terminal B (xterm.js)                  │
│  └── Memory Sidebar (Live + Archive)        │
└─────────────────────────────────────────────┘
              ↕ WebSocket/REST
┌─────────────────────────────────────────────┐
│  Backend (FastAPI)                          │
│  ├── REST API endpoints                     │
│  ├── WebSocket broadcast                    │
│  └── TeamAgent core integration             │
└─────────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────────┐
│  Data Layer                                 │
│  ├── SQLite (Q&A archive)                   │
│  └── Mnemosyne (Memory banks)               │
└─────────────────────────────────────────────┘
```

## Quick Start

### Docker Compose (Recommended)

The easiest way to run the full stack:

```bash
docker compose up --build
```

This starts both services:
- **Backend** (FastAPI) on `http://localhost:8000`
- **Frontend** (React + Vite) on `http://localhost:3000`

Data is persisted in a `teamagent-data` Docker volume.

To stop:

```bash
docker compose down
```

### Manual Setup

### 1. Install Backend Dependencies

```bash
cd web/backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd web/frontend
npm install
```

### 3. Start Backend Server

```bash
cd web/backend
python api.py
```

Backend runs on `http://localhost:8000`

### 4. Start Frontend Dev Server

```bash
cd web/frontend
npm run dev
```

Frontend runs on `http://localhost:3000`

### 5. Open in Browser

Visit `http://localhost:3000` to see the demo!

## Usage Demo

### Scenario: Variable Collaboration

**Terminal A (Engineer Alice):**
```
A> ask variable x equals 10
```

**Terminal B (Engineer Bob):**
```
B> search variable
```
→ Instantly sees Alice's question!

```
B> ask what is x plus 5
```

This demonstrates:
- Real-time memory synchronization
- Cross-engineer knowledge sharing
- Instant search and recall

### Available Commands

Both terminals support:

| Command | Description | Example |
|---------|-------------|---------|
| `ask <question>` | Ask a question | `ask How does auth work?` |
| `search <query>` | Search Q&A archive | `search authentication` |
| `recent` | Show recent questions | `recent` |
| `memory` | View memory entries | `memory` |
| `help` | Show help | `help` |
| `clear` | Clear terminal | `clear` |

## API Endpoints

### REST API

- `POST /engineers/` - Create engineer profile
- `GET /engineers/{id}` - Get engineer details
- `GET /teams/{id}` - Get team details
- `POST /qa/ask` - Ask a question
- `POST /qa/answer` - Answer a question
- `GET /qa/search` - Search Q&A
- `GET /qa/recent` - Get recent Q&A
- `GET /memory/{team_id}/{engineer_id}` - Get memory entries
- `POST /command/execute` - Execute TeamAgent command

### WebSocket

- `WS /ws/{engineer_id}` - Real-time updates

Messages:
- `new_question` - Broadcast when question asked
- `new_answer` - Broadcast when answer added
- `command_executed` - Broadcast command results

## Project Structure

```
web/
├── backend/
│   ├── api.py              # FastAPI server
│   └── requirements.txt    # Python dependencies
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Terminal.jsx        # xterm.js terminal
    │   │   ├── Terminal.css
    │   │   ├── MemorySidebar.jsx   # Memory visualization
    │   │   └── MemorySidebar.css
    │   ├── App.jsx                  # Main app
    │   ├── App.css
    │   └── main.jsx                 # Entry point
    ├── index.html
    ├── vite.config.js
    └── package.json
```

## Customization

### Colors

Edit terminal colors in `Terminal.jsx`:

```javascript
theme: {
  background: '#0a0e27',
  foreground: color,  // Passed as prop
  cursor: color,
  // ... more colors
}
```

### Engineer Names

Modify in `App.jsx`:

```javascript
// Engineer A
name: 'Alice (Engineer A)',
email: 'alice@teamagent.demo',

// Engineer B  
name: 'Bob (Engineer B)',
email: 'bob@teamagent.demo',
```

## Production Deployment

### Backend

```bash
cd web/backend
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app
```

### Frontend

```bash
cd web/frontend
npm run build
# Serve the 'dist' folder with nginx or similar
```

### Environment Variables

Create `.env` files:

**Backend:**
```bash
DATABASE_PATH=/path/to/teamagent.db
CORS_ORIGINS=https://yourdomain.com
```

**Frontend:**
```bash
VITE_API_URL=https://api.yourdomain.com
```

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- Frontend: Vite automatically reloads on file changes
- Backend: Use `uvicorn api:app --reload`

### Debugging WebSocket

Open browser console to see WebSocket messages:

```javascript
// Messages appear in Network tab → WS
```

### Add New Commands

1. Add command handler in `backend/api.py` → `execute_command()`
2. Terminal will automatically support it

## Showcase Features

This demo highlights:

1. **Instant Memory Sync** - Questions asked in Terminal A appear immediately in Terminal B's search
2. **Live Activity Feed** - Right sidebar shows all commands and events in real-time
3. **Persistent Archive** - All Q&A saved to SQLite and searchable
4. **Multi-Engineer Simulation** - Two independent terminals with shared memory
5. **Terminal Authenticity** - Real xterm.js with full terminal features

## Troubleshooting

### Backend won't start
- Check Python dependencies: `pip install -r requirements.txt`
- Verify database path is accessible
- Check port 8000 is available

### Frontend build errors
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Check Node.js version (need v16+)

### WebSocket connection fails
- Verify backend is running on port 8000
- Check browser console for errors
- Try disabling browser extensions

## Future Enhancements

- [ ] AI agent integration (connect to Red Hat Claude API)
- [ ] Multi-tab support (more than 2 engineers)
- [ ] File sharing between terminals
- [ ] Code snippet highlighting
- [ ] Export Q&A as markdown
- [ ] Voice commands (Web Speech API)

## License

MIT - Same as TeamAgent core

---

**Built with:** React, Vite, xterm.js, FastAPI, WebSocket, SQLite
