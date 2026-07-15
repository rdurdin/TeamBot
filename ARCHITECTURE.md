# TeamAgent Web Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   React App (Port 3000)                    │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │  Terminal A  │  │  Terminal B  │  │ Memory Sidebar  │ │ │
│  │  │  (xterm.js)  │  │  (xterm.js)  │  │                 │ │ │
│  │  │              │  │              │  │ • Live Feed     │ │ │
│  │  │ Engineer A   │  │ Engineer B   │  │ • Q&A Archive   │ │ │
│  │  │ ID: alice-1  │  │ ID: bob-2    │  │ • Stats         │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘ │ │
│  │         │                  │                    │          │ │
│  │         └──────────────────┴────────────────────┘          │ │
│  │                            │                                │ │
│  │                    ┌───────▼────────┐                      │ │
│  │                    │  App.jsx       │                      │ │
│  │                    │  - State Mgmt  │                      │ │
│  │                    │  - WS Clients  │                      │ │
│  │                    │  - API Calls   │                      │ │
│  │                    └───────┬────────┘                      │ │
│  └────────────────────────────┼─────────────────────────────┘ │
└────────────────────────────────┼───────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
          REST API (HTTP)    WebSocket      WebSocket
         /api/engineers      /ws/alice-1    /ws/bob-2
         /api/qa/ask
         /api/qa/search
                 │               │               │
                 └───────────────▼───────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (Port 8000)                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                     API Endpoints                          │ │
│  │                                                             │ │
│  │  POST /engineers/        GET  /qa/search                  │ │
│  │  POST /qa/ask            GET  /qa/recent                  │ │
│  │  POST /qa/answer         GET  /memory/{team}/{eng}        │ │
│  │  POST /command/execute   ...                              │ │
│  └─────────────────────────┬───────────────────────────────┘ │
│                            │                                   │
│  ┌─────────────────────────▼───────────────────────────────┐ │
│  │              WebSocket Connection Manager                 │ │
│  │                                                            │ │
│  │  active_connections = {                                   │ │
│  │    "alice-1": WebSocket<connection>,                     │ │
│  │    "bob-2": WebSocket<connection>                        │ │
│  │  }                                                         │ │
│  │                                                            │ │
│  │  Methods:                                                  │ │
│  │  • broadcast(message) → All engineers                     │ │
│  │  • send_personal(engineer_id, message)                    │ │
│  └─────────────────────────┬───────────────────────────────┘ │
│                            │                                   │
│  ┌─────────────────────────▼───────────────────────────────┐ │
│  │              TeamAgent Core Integration                    │ │
│  │                                                            │ │
│  │  from core.engineer import Engineer                       │ │
│  │  from core.team import Team                               │ │
│  │  from core.qa_archive import QAArchive                    │ │
│  │  from core.memory_manager import MemoryManager            │ │
│  └─────────────────────────┬───────────────────────────────┘ │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                               │ SQLite Connection
                               │
┌──────────────────────────────▼─────────────────────────────────┐
│                     Data Layer                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              SQLite Database (teamagent.db)               │ │
│  │                                                            │ │
│  │  Tables:                                                   │ │
│  │  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │   engineers    │  │    teams     │  │ team_members │ │ │
│  │  ├────────────────┤  ├──────────────┤  ├──────────────┤ │ │
│  │  │ id (PK)        │  │ id (PK)      │  │ team_id      │ │ │
│  │  │ name           │  │ name         │  │ engineer_id  │ │ │
│  │  │ email          │  │ description  │  │ role         │ │ │
│  │  │ git_username   │  │ codebase     │  │ joined_at    │ │ │
│  │  └────────────────┘  └──────────────┘  └──────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐│ │
│  │  │                  qa_entries                           ││ │
│  │  ├──────────────────────────────────────────────────────┤│ │
│  │  │ id (PK)                                               ││ │
│  │  │ team_id (FK)                                          ││ │
│  │  │ question                                              ││ │
│  │  │ answer                                                ││ │
│  │  │ asked_by (FK → engineers)                            ││ │
│  │  │ answered_by (FK → engineers)                         ││ │
│  │  │ asked_at, answered_at                                 ││ │
│  │  │ status (open/answered)                                ││ │
│  │  │ tags, context_json                                    ││ │
│  │  └──────────────────────────────────────────────────────┘│ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐│ │
│  │  │           qa_fts (FTS5 Virtual Table)                 ││ │
│  │  ├──────────────────────────────────────────────────────┤│ │
│  │  │ qa_id (UNINDEXED)                                     ││ │
│  │  │ question (INDEXED for full-text search)               ││ │
│  │  │ answer (INDEXED)                                      ││ │
│  │  │ tags (INDEXED)                                        ││ │
│  │  │                                                        ││ │
│  │  │ Triggers: Auto-sync with qa_entries                   ││ │
│  │  │ - INSERT → Add to FTS                                 ││ │
│  │  │ - UPDATE → Re-index                                   ││ │
│  │  │ - DELETE → Remove from FTS                            ││ │
│  │  └──────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Mnemosyne Memory Banks                       │ │
│  │                                                            │ │
│  │  Team-scoped memory stores:                               │ │
│  │  ┌──────────────────────────────────────────────────────┐│ │
│  │  │  MemoryEntry {                                        ││ │
│  │  │    key: string                                        ││ │
│  │  │    value: any                                         ││ │
│  │  │    context: dict                                      ││ │
│  │  │    timestamp: datetime                                ││ │
│  │  │  }                                                     ││ │
│  │  └──────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Ask Question Flow

```
Terminal A (Engineer Alice)
    │
    │ User types: "ask variable x equals 10"
    │
    ▼
App.jsx: executeCommand()
    │
    │ POST /api/command/execute
    │ {
    │   command: "ask variable x equals 10",
    │   engineer_id: "alice-1",
    │   team_id: "demo-team-001"
    │ }
    │
    ▼
FastAPI: execute_command()
    │
    │ Parse command → "ask"
    │ Extract args → "variable x equals 10"
    │
    ▼
QAArchive.add_question()
    │
    │ INSERT INTO qa_entries
    │ (question, asked_by, team_id, ...)
    │
    │ Trigger: INSERT INTO qa_fts
    │
    ▼
WebSocket.broadcast()
    │
    ├──► Terminal A: Shows result
    │
    └──► Terminal B: Receives notification
         │
         │ {
         │   type: "new_question",
         │   data: {
         │     id: "qa-123",
         │     question: "variable x equals 10",
         │     asked_by: "alice-1"
         │   }
         │ }
         │
         ▼
    Memory Sidebar: Updates live feed
```

### 2. Search Flow

```
Terminal B (Engineer Bob)
    │
    │ User types: "search variable"
    │
    ▼
App.jsx: executeCommand()
    │
    │ POST /api/command/execute
    │ {
    │   command: "search variable",
    │   engineer_id: "bob-2",
    │   team_id: "demo-team-001"
    │ }
    │
    ▼
FastAPI: execute_command()
    │
    │ Parse command → "search"
    │ Extract args → "variable"
    │
    ▼
QAArchive.search()
    │
    │ Tokenize query → ["variable"]
    │ FTS5 query: variable
    │
    │ SELECT q.*
    │ FROM qa_fts f
    │ JOIN qa_entries q ON f.qa_id = q.id
    │ WHERE q.team_id = ? AND qa_fts MATCH ?
    │ ORDER BY f.rank LIMIT 10
    │
    ▼
Results returned to Terminal B
    │
    │ Found 1 result(s):
    │ 1. ? variable x equals 10
    │    Asked by: alice-1
    │
    ▼
Terminal B displays results instantly!
```

### 3. WebSocket Real-time Sync

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Terminal A  │         │   FastAPI    │         │  Terminal B  │
│   (Alice)    │         │   Server     │         │    (Bob)     │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ WS Connect             │                        │
       ├───────────────────────►│                        │
       │ /ws/alice-1            │                        │
       │                        │                        │
       │                        │         WS Connect     │
       │                        │◄───────────────────────┤
       │                        │         /ws/bob-2      │
       │                        │                        │
       │ Command: ask X         │                        │
       ├───────────────────────►│                        │
       │                        │                        │
       │                        │ broadcast({            │
       │                        │   type: "new_question" │
       │                        │ })                     │
       │                        │                        │
       │◄───────────────────────┤                        │
       │   WS message           │                        │
       │                        ├───────────────────────►│
       │                        │   WS message           │
       │                        │                        │
       │                        │                        ▼
       │                        │              Sidebar updates!
       │                        │              Shows new question
       │                        │              from Alice
```

## Component Architecture

### Frontend Components

```
App.jsx
├── Header
│   ├── Title
│   └── Tagline
│
├── TerminalsContainer
│   ├── TerminalWrapper (Engineer A)
│   │   ├── Label
│   │   └── Terminal
│   │       ├── xterm instance
│   │       ├── FitAddon
│   │       ├── Command buffer
│   │       └── Event handlers
│   │
│   └── TerminalWrapper (Engineer B)
│       ├── Label
│       └── Terminal
│           └── (same as above)
│
├── MemorySidebar
│   ├── Header
│   │   ├── Title
│   │   └── Stats
│   │       ├── Live Events counter
│   │       └── Q&A Archive counter
│   │
│   ├── Tabs
│   │   ├── Live Feed (active)
│   │   └── Q&A Archive
│   │
│   └── Content
│       ├── Live Feed View
│       │   └── MemoryItem[]
│       │       ├── Header (engineer badge, timestamp)
│       │       └── Content (command, result, or event)
│       │
│       └── Q&A Archive View
│           └── QAItem[]
│               ├── Status icon
│               ├── Question
│               ├── Answer (if exists)
│               └── Metadata
│
└── Footer
    └── Demo Instructions
```

### Backend Structure

```
api.py
├── FastAPI app initialization
├── CORS middleware
├── Database connection
│
├── ConnectionManager (WebSocket)
│   ├── active_connections: Dict[str, WebSocket]
│   ├── connect()
│   ├── disconnect()
│   ├── broadcast()
│   └── send_personal()
│
├── Pydantic Models
│   ├── EngineerCreate
│   ├── QuestionCreate
│   ├── AnswerCreate
│   └── CommandExecute
│
├── REST Endpoints
│   ├── POST /engineers/
│   ├── GET  /engineers/{id}
│   ├── GET  /teams/{id}
│   ├── POST /qa/ask
│   ├── POST /qa/answer
│   ├── GET  /qa/search
│   ├── GET  /qa/recent
│   ├── GET  /memory/{team_id}/{engineer_id}
│   └── POST /command/execute
│
└── WebSocket Endpoint
    └── WS /ws/{engineer_id}
```

## State Management

### Frontend State (App.jsx)

```javascript
State:
├── engineerA: Engineer | null
├── engineerB: Engineer | null
├── memories: Memory[]
├── qaEntries: QAEntry[]
├── wsA: WebSocket | null
└── wsB: WebSocket | null

Effects:
├── useEffect([]) → Initialize engineers
├── useEffect([engineerA, engineerB]) → Setup WebSocket
└── useEffect([message]) → Handle WS messages

Actions:
├── executeCommand(command, engineerId, engineerName)
├── handleWebSocketMessage(message, engineer)
├── loadRecentQA()
└── addMemoryEntry(entry)
```

### Backend State

```python
Global:
├── db_conn: sqlite3.Connection
└── manager: ConnectionManager

Per Request:
├── engineer: Engineer
├── team: Team
├── qa: QAArchive
└── memory: MemoryManager
```

## Security Considerations

### Current Implementation (Demo)
- CORS: Allow all origins (`*`)
- No authentication
- No rate limiting
- No input sanitization beyond Pydantic

### Production Requirements
```python
# CORS
allow_origins=[
    "https://teamagent.yourdomain.com"
]

# Authentication
@app.middleware("http")
async def authenticate(request: Request, call_next):
    token = request.headers.get("Authorization")
    # Verify JWT token
    # ...

# Rate Limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/qa/ask")
@limiter.limit("10/minute")
async def ask_question(...):
    # ...

# Input Sanitization
import bleach
question = bleach.clean(question_data.question)
```

## Performance Optimizations

### Database
- WAL mode enabled for concurrent reads
- FTS5 for fast full-text search
- Indexes on foreign keys
- Connection pooling (future)

### WebSocket
- Message batching (future)
- Compression for large payloads
- Reconnection logic with exponential backoff

### Frontend
- React.memo for Terminal components
- Debounced search input
- Virtual scrolling for large memory lists (future)
- Code splitting with React.lazy

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Production                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │                    Nginx (Reverse Proxy)                ││
│  │                    Port 80/443 (HTTPS)                  ││
│  │                                                          ││
│  │  /          → Frontend (static files)                   ││
│  │  /api/*     → Backend (FastAPI)                         ││
│  │  /ws/*      → WebSocket (FastAPI)                       ││
│  └────────────┬──────────────────────────┬─────────────────┘│
│               │                          │                   │
│  ┌────────────▼──────────┐  ┌───────────▼────────────────┐ │
│  │  Frontend (Static)    │  │  Backend (Gunicorn)        │ │
│  │  - React build        │  │  - 4 workers               │ │
│  │  - Gzip compressed    │  │  - Uvicorn worker class    │ │
│  │  - Cached             │  │  - Port 8000 (internal)    │ │
│  └───────────────────────┘  └────────────┬───────────────┘ │
│                                           │                  │
│                              ┌────────────▼───────────────┐ │
│                              │  SQLite + Mnemosyne        │ │
│                              │  /var/lib/teamagent/       │ │
│                              └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Metrics to Track
- WebSocket connections (active count)
- Messages per second (throughput)
- API response times (latency)
- Database query times
- Error rates
- Memory usage

### Logging
```python
import logging

logger = logging.getLogger("teamagent")

# API calls
logger.info(f"Engineer {engineer_id} asked: {question}")

# WebSocket events
logger.debug(f"WS broadcast to {len(connections)} clients")

# Errors
logger.error(f"Failed to save Q&A: {error}", exc_info=True)
```

---

This architecture supports:
✓ Real-time collaboration
✓ Persistent memory
✓ Fast search (FTS5)
✓ Scalable WebSocket
✓ Clean separation of concerns
✓ Easy to extend
