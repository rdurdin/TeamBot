"""FastAPI backend for TeamAgent web interface."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engineer import Engineer
from core.team import Team
from core.qa_archive import QAArchive
from core.memory_manager import MemoryManager
from storage.schema import init_database

# Lazy import AI agent to avoid dependency errors
RedHatAIAgent = None
MnemosyneAIAgent = None

app = FastAPI(title="TeamAgent API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection
db_conn = init_database()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, engineer_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[engineer_id] = websocket

    def disconnect(self, engineer_id: str):
        if engineer_id in self.active_connections:
            del self.active_connections[engineer_id]

    async def broadcast(self, message: dict):
        """Broadcast to all connected engineers."""
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except:
                pass

    async def send_personal(self, engineer_id: str, message: dict):
        """Send message to specific engineer."""
        if engineer_id in self.active_connections:
            try:
                await self.active_connections[engineer_id].send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class EngineerCreate(BaseModel):
    name: str
    email: str
    git_username: Optional[str] = None

class QuestionCreate(BaseModel):
    question: str
    engineer_id: str
    team_id: str

class AnswerCreate(BaseModel):
    qa_id: str
    answer: str
    engineer_id: str

class CommandExecute(BaseModel):
    command: str
    engineer_id: str
    team_id: str

# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "TeamAgent API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/engineers/")
async def create_engineer(engineer: EngineerCreate):
    """Create or get engineer profile."""
    try:
        eng = Engineer.get_or_create(
            conn=db_conn,
            name=engineer.name,
            email=engineer.email,
            git_username=engineer.git_username
        )
        return {
            "id": eng.id,
            "name": eng.name,
            "email": eng.email,
            "git_username": eng.git_username
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/engineers/{engineer_id}")
async def get_engineer(engineer_id: str):
    """Get engineer by ID."""
    engineer = Engineer.get_by_id(db_conn, engineer_id)
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")

    return {
        "id": engineer.id,
        "name": engineer.name,
        "email": engineer.email,
        "git_username": engineer.git_username
    }

@app.get("/teams/{team_id}")
async def get_team(team_id: str):
    """Get team by ID."""
    team = Team.get_by_id(db_conn, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = team.get_members()

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "codebase_path": team.codebase_path,
        "members": [{"id": m.id, "name": m.name, "email": m.email} for m in members]
    }

@app.post("/qa/ask")
async def ask_question(question_data: QuestionCreate):
    """Ask a new question."""
    try:
        qa = QAArchive(db_conn)
        entry = qa.ask(
            team_id=question_data.team_id,
            question=question_data.question,
            asked_by=question_data.engineer_id
        )

        # Broadcast to all connected engineers
        await manager.broadcast({
            "type": "new_question",
            "data": {
                "id": entry.id,
                "question": entry.question,
                "asked_by": question_data.engineer_id,
                "timestamp": entry.asked_at.isoformat()
            }
        })

        return {
            "id": entry.id,
            "question": entry.question,
            "status": entry.status,
            "asked_at": entry.asked_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/qa/answer")
async def answer_question(answer_data: AnswerCreate):
    """Answer a question."""
    try:
        qa = QAArchive(db_conn)
        entry = qa.answer(
            qa_id=answer_data.qa_id,
            answer=answer_data.answer,
            answered_by=answer_data.engineer_id
        )

        # Broadcast to all connected engineers
        await manager.broadcast({
            "type": "new_answer",
            "data": {
                "qa_id": entry.id,
                "question": entry.question,
                "answer": entry.answer,
                "answered_by": answer_data.engineer_id,
                "timestamp": entry.answered_at.isoformat() if entry.answered_at else None
            }
        })

        return {
            "id": entry.id,
            "question": entry.question,
            "answer": entry.answer,
            "status": entry.status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/qa/search")
async def search_qa(team_id: str, query: str, limit: int = 10):
    """Search Q&A entries."""
    try:
        qa = QAArchive(db_conn)
        results = qa.search(team_id=team_id, query=query, limit=limit)

        return {
            "results": [
                {
                    "id": r.id,
                    "question": r.question,
                    "answer": r.answer,
                    "status": r.status,
                    "asked_at": r.asked_at.isoformat(),
                    "answered_at": r.answered_at.isoformat() if r.answered_at else None
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/qa/recent")
async def recent_qa(team_id: str, limit: int = 10):
    """Get recent Q&A entries."""
    try:
        qa = QAArchive(db_conn)
        results = qa.list_recent(team_id=team_id, limit=limit)

        return {
            "results": [
                {
                    "id": r.id,
                    "question": r.question,
                    "answer": r.answer,
                    "status": r.status,
                    "asked_at": r.asked_at.isoformat(),
                    "answered_at": r.answered_at.isoformat() if r.answered_at else None
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/memory/{team_id}/{engineer_id}")
async def get_memory(team_id: str, engineer_id: str):
    """Get memory entries for engineer in team."""
    try:
        team = Team.get_by_id(db_conn, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        memory = team.get_memory(engineer_id)
        memories = memory.get_all()

        return {
            "memories": [
                {
                    "key": m.key,
                    "value": m.value,
                    "context": m.context,
                    "timestamp": m.timestamp.isoformat() if hasattr(m.timestamp, 'isoformat') else str(m.timestamp)
                }
                for m in memories
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class MessageArchive(BaseModel):
    message: str
    engineer_id: str
    team_id: str
    message_type: str = "manual"

@app.post("/message/archive")
async def archive_message(msg: MessageArchive):
    """Archive a manual message to team memory (hive mind)."""
    try:
        from core.mnemosyne_ai_agent import MnemosyneAIAgent
        team = Team.get_by_id(db_conn, msg.team_id)

        ai_agent = MnemosyneAIAgent(
            team_id=msg.team_id,
            engineer_id=msg.engineer_id,
            team_name=team.name if team else "Team"
        )

        success = ai_agent.archive_message(msg.message, msg.message_type)

        return {
            "success": success,
            "message": "Archived to team memory" if success else "Archive failed"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/command/execute")
async def execute_command(cmd: CommandExecute):
    """Execute a TeamAgent command and return result."""
    try:
        result = {
            "command": cmd.command,
            "timestamp": datetime.now().isoformat(),
            "engineer_id": cmd.engineer_id
        }

        # Parse command
        parts = cmd.command.strip().split(None, 1)
        if not parts:
            result["output"] = "No command provided"
            return result

        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        qa = QAArchive(db_conn)
        team = Team.get_by_id(db_conn, cmd.team_id)

        if command == "ask":
            entry = qa.ask(
                team_id=cmd.team_id,
                question=args,
                asked_by=cmd.engineer_id
            )
            result["output"] = f"Question saved: {entry.id}\n{entry.question}"
            result["type"] = "question"
            result["qa_id"] = entry.id

            # Broadcast
            await manager.broadcast({
                "type": "command_executed",
                "data": result
            })

        elif command == "search":
            results = qa.search(team_id=cmd.team_id, query=args, limit=5)
            output = f"Found {len(results)} result(s):\n\n"
            for i, r in enumerate(results, 1):
                status = "✓" if r.status == "answered" else "?"
                output += f"{i}. {status} {r.question}\n"
                if r.answer:
                    output += f"   A: {r.answer[:100]}...\n"
            result["output"] = output
            result["type"] = "search"

        elif command == "recent":
            # Show recent Mnemosyne memories instead of Q&A
            try:
                from core.mnemosyne_ai_agent import MnemosyneAIAgent
                ai_agent = MnemosyneAIAgent(
                    team_id=cmd.team_id,
                    engineer_id=cmd.engineer_id,
                    team_name=team.name if team else "Team"
                )

                # Get recent memories
                memories = ai_agent.search_memories("", limit=10)

                if not memories:
                    output = "No recent team memories yet.\n\n"
                    output += "Start building team knowledge:\n"
                    output += "  - Use 'log <info>' to manually archive\n"
                    output += "  - Use 'ai <question>' to ask (auto-archives)\n"
                else:
                    output = f"Recent team memories ({len(memories)}):\n\n"
                    for i, mem in enumerate(memories, 1):
                        content = mem.get('content', '')[:150]
                        timestamp = mem.get('timestamp', 'unknown')
                        source = mem.get('source', 'unknown')

                        # Format nicely
                        if source == 'logged-info':
                            icon = "📝"
                        elif source == 'ai-conversation':
                            icon = "🤖"
                        else:
                            icon = "💬"

                        output += f"{i}. {icon} [{timestamp[:10]}] {content}...\n\n"

                result["output"] = output
                result["type"] = "recent"
            except Exception as e:
                # Fallback to Q&A if Mnemosyne fails
                results = qa.list_recent(team_id=cmd.team_id, limit=5)
                output = f"Recent Q&A ({len(results)}):\n\n"
                for i, r in enumerate(results, 1):
                    status = "✓" if r.status == "answered" else "?"
                    output += f"{i}. {status} {r.question}\n"
                result["output"] = output
                result["type"] = "recent"

        elif command == "memory":
            # Redirect to Mnemosyne memories instead of legacy memory
            try:
                from core.mnemosyne_ai_agent import MnemosyneAIAgent
                ai_agent = MnemosyneAIAgent(
                    team_id=cmd.team_id,
                    engineer_id=cmd.engineer_id,
                    team_name=team.name if team else "Team"
                )

                # Get stats
                stats = ai_agent.get_memory_stats()
                total = stats.get('total_memories', 0) if isinstance(stats, dict) else 0

                # Get recent memories
                memories = ai_agent.search_memories("", limit=5)

                output = f"Team Memory (Mnemosyne Hive Mind)\n\n"
                output += f"📊 Total archived: {total} conversations\n"
                output += f"👥 Shared across all engineers\n\n"

                if memories:
                    output += "Recent memories:\n\n"
                    for i, mem in enumerate(memories[:5], 1):
                        content = mem.get('content', '')[:100]
                        source = mem.get('source', 'unknown')
                        output += f"{i}. ({source}) {content}...\n"
                    output += f"\nUse 'memories <query>' to search"
                else:
                    output += "No memories yet. Use 'log <info>' to start building team knowledge."

                result["output"] = output
                result["type"] = "memory"
            except Exception as e:
                # Fallback to legacy memory
                memory = team.get_memory(cmd.engineer_id)
                memories = memory.get_all()
                output = f"Legacy Memory entries ({len(memories)}):\n\n"
                for m in memories[:10]:
                    output += f"• {m.key}: {m.value}\n"
                result["output"] = output
                result["type"] = "memory"

        elif command == "ai":
            # Use Mnemosyne AI agent for automatic memory archiving
            try:
                # Import Mnemosyne AI agent directly (no global needed)
                from core.mnemosyne_ai_agent import MnemosyneAIAgent

                # Create Mnemosyne-backed AI agent
                ai_agent = MnemosyneAIAgent(
                    team_id=cmd.team_id,
                    engineer_id=cmd.engineer_id,
                    team_name=team.name if team else "Team"
                )

                # Get context from recent Q&A
                context_qa = qa.list_recent(team_id=cmd.team_id, limit=5)
                context_list = [
                    {"id": r.id, "question": r.question, "answer": r.answer}
                    for r in context_qa if r.answer
                ]

                # Answer question - Mnemosyne automatically:
                # 1. Recalls relevant memories
                # 2. Generates answer with full context
                # 3. Archives the conversation
                response = ai_agent.answer_question(
                    question=args,
                    context_qa=context_list,
                    team_name=team.name if team else "Team"
                )

                # Get memory stats
                stats = ai_agent.get_memory_stats()
                total_memories = stats.get('total_memories', 0) if isinstance(stats, dict) else 0

                output = f"🤖 AI Response"
                if total_memories > 0:
                    output += f" (learned from {total_memories} past conversations)"
                output += f":\n\n{response.answer}"

                result["output"] = output
                result["type"] = "ai"

            except Exception as e:
                # Fall back to error message if AI not available
                import traceback
                error_detail = traceback.format_exc()
                output = f"⚠️ AI not available: {str(e)}\n\n"
                output += "To enable AI:\n"
                output += "1. Set MODEL_API environment variable\n"
                output += "2. Set USER_KEY environment variable\n"
                output += "3. Set MODEL_ID environment variable\n\n"
                output += "For now, use 'ask' to save questions and 'search' to find answers."
                result["output"] = output
                result["type"] = "error"
                print(f"AI Error: {error_detail}")

        elif command == "log":
            # Log information to hive mind (manual archiving)
            try:
                from core.mnemosyne_ai_agent import MnemosyneAIAgent
                ai_agent = MnemosyneAIAgent(
                    team_id=cmd.team_id,
                    engineer_id=cmd.engineer_id,
                    team_name=team.name if team else "Team"
                )

                if not args:
                    output = "Usage: log <information>\n\nExample: log variable x = 5"
                else:
                    # Archive to hive mind
                    engineer = Engineer.get_by_id(db_conn, cmd.engineer_id)
                    engineer_name = engineer.name if engineer else cmd.engineer_id

                    message = f"[{engineer_name}] {args}"
                    success = ai_agent.archive_message(message, "logged-info")

                    if success:
                        output = f"✓ Logged to team memory:\n\n{args}\n\nAll engineers can now recall this information."
                    else:
                        output = "Failed to log to memory"

                result["output"] = output
                result["type"] = "log"
            except Exception as e:
                result["output"] = f"Error: {e}"
                result["type"] = "error"

        elif command == "memories":
            # Search Mnemosyne archived conversations
            try:
                from core.mnemosyne_ai_agent import MnemosyneAIAgent
                ai_agent = MnemosyneAIAgent(
                    team_id=cmd.team_id,
                    engineer_id=cmd.engineer_id,
                    team_name=team.name if team else "Team"
                )

                if args:
                    # Search memories
                    memories = ai_agent.search_memories(args, limit=10)
                    output = f"Found {len(memories)} archived conversations matching '{args}':\n\n"
                    for i, mem in enumerate(memories, 1):
                        content = mem.get('content', '')[:200]
                        timestamp = mem.get('timestamp', 'unknown')
                        source = mem.get('source', 'unknown')
                        output += f"{i}. [{timestamp}] ({source})\n{content}...\n\n"
                else:
                    # Show stats
                    stats = ai_agent.get_memory_stats()
                    if 'error' in stats:
                        output = f"Memory stats unavailable: {stats['error']}"
                    else:
                        total = stats.get('total_memories', 0)
                        output = f"Mnemosyne Memory Stats (Team-Wide Hive Mind):\n\n"
                        output += f"  Total archived conversations: {total}\n"
                        output += f"  Team: {team.name if team else 'Unknown'}\n"
                        output += f"  Shared across all engineers\n\n"
                        output += f"Commands:\n"
                        output += f"  memories <query> - Search team memories\n"
                        output += f"  log <info> - Manually log information\n"
                        output += f"  ai <question> - AI auto-recalls memories"

                result["output"] = output
                result["type"] = "memories"
            except Exception as e:
                import traceback
                result["output"] = f"Error accessing memories: {e}\n\n{traceback.format_exc()}"
                result["type"] = "error"

        else:
            result["output"] = f"Unknown command: {command}\n\nAvailable commands:\n  ask <question> - Save question to Q&A\n  search <query> - Search Q&A archive\n  recent - Show recent Q&A\n  memory - Show legacy memory\n  ai <question> - Ask AI (auto-recalls team memories)\n  log <info> - Manually log to hive mind\n  memories [query] - View/search team-wide memories"

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/{engineer_id}")
async def websocket_endpoint(websocket: WebSocket, engineer_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(engineer_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle incoming messages
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(engineer_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
