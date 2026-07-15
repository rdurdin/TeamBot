"""AI agent with Mnemosyne memory integration - conversations auto-archived."""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from mnemosyne import Mnemosyne, remember, recall
    MNEMOSYNE_AVAILABLE = True
except ImportError:
    MNEMOSYNE_AVAILABLE = False
    print("Warning: Mnemosyne not available. Install with: pip install mnemosyne-memory")

from core.redhat_ai_agent import RedHatAIAgent, AIResponse


class MnemosyneAIAgent:
    """
    AI agent with automatic conversation memory using Mnemosyne.

    All conversations are automatically archived and used to build context.
    The AI gets smarter over time as it learns from past interactions.
    """

    def __init__(
        self,
        team_id: str,
        engineer_id: str,
        team_name: str = "Team",
        api_url: Optional[str] = None,
        user_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize AI agent with Mnemosyne memory.

        Args:
            team_id: Team identifier for memory isolation
            engineer_id: Engineer identifier
            team_name: Human-readable team name
            api_url: Red Hat Claude API URL
            user_key: API authentication key
            model: Model ID
        """
        self.team_id = team_id
        self.engineer_id = engineer_id
        self.team_name = team_name

        # Initialize base AI agent
        self.ai_agent = RedHatAIAgent(
            api_url=api_url,
            user_key=user_key,
            model=model
        )

        # Initialize Mnemosyne memory with TEAM-WIDE sharing (hive mind)
        self.memory = None
        if MNEMOSYNE_AVAILABLE:
            try:
                # Use team_id for SHARED memory - all engineers see all memories
                # session_id is team-wide, not per-engineer
                self.memory = Mnemosyne(
                    session_id=team_id,  # SHARED across all engineers
                    bank=f"teamagent_{team_id}",
                    author_id=engineer_id,  # Track who wrote it
                    author_type="engineer",
                    channel_id=team_id
                )
            except Exception as e:
                print(f"Warning: Could not initialize Mnemosyne: {e}")

    def answer_question(
        self,
        question: str,
        context_qa: List[dict] = None,
        team_name: str = None,
        memory_context: str = "",
    ) -> AIResponse:
        """Answer question using Mnemosyne memory + Q&A context.

        Automatically:
        1. Recalls relevant past conversations from Mnemosyne
        2. Includes Q&A context
        3. Generates answer
        4. Archives the conversation to Mnemosyne

        Args:
            question: User's question
            context_qa: Optional Q&A entries for context
            team_name: Team name override
            memory_context: Legacy memory context (ignored if Mnemosyne available)

        Returns:
            AIResponse with answer, sources, and confidence
        """
        context_qa = context_qa or []
        team_name = team_name or self.team_name

        # 1. Recall relevant memories from Mnemosyne (TEAM-WIDE)
        mnemosyne_context = ""
        if self.memory:
            try:
                # Search for relevant past conversations across ALL engineers
                # Don't filter by session_id to get team-wide memories
                memories = self.memory.recall(
                    query=question,
                    top_k=15
                    # Note: No session_id filter = team-wide recall
                )

                if memories:
                    memory_entries = []
                    for i, mem in enumerate(memories, 1):
                        content = mem.get('content', '')
                        timestamp = mem.get('timestamp', '')
                        source = mem.get('source', 'conversation')

                        # Format memory entry
                        entry = f"[Memory {i} - {timestamp}] ({source})\n{content}"
                        memory_entries.append(entry)

                    mnemosyne_context = "\n\n".join(memory_entries)
            except Exception as e:
                print(f"Warning: Mnemosyne recall failed: {e}")

        # Use Mnemosyne context if available, otherwise fall back to legacy
        final_memory_context = mnemosyne_context if mnemosyne_context else memory_context

        # 2. Get AI response with memory context
        response = self.ai_agent.answer_question(
            question=question,
            context_qa=context_qa,
            team_name=team_name,
            memory_context=final_memory_context
        )

        # 3. Archive the conversation to Mnemosyne
        if self.memory:
            try:
                # Store the Q&A exchange
                conversation = f"""Question: {question}

Answer: {response.answer}

Engineer: {self.engineer_id}
Team: {team_name}
Timestamp: {datetime.now().isoformat()}"""

                self.memory.remember(
                    content=conversation,
                    importance=0.8,
                    source="ai-conversation",
                    metadata={
                        "question": question,
                        "engineer_id": self.engineer_id,
                        "team_id": self.team_id,
                        "confidence": response.confidence,
                        "timestamp": datetime.now().isoformat()
                    }
                )

                # Also remember just the question for quick lookup
                self.memory.remember(
                    content=f"Q: {question}",
                    importance=0.6,
                    source="question",
                    metadata={
                        "type": "question",
                        "engineer_id": self.engineer_id,
                        "timestamp": datetime.now().isoformat()
                    }
                )

                # Remember the answer separately for better retrieval
                self.memory.remember(
                    content=f"A: {response.answer}",
                    importance=0.7,
                    source="ai-answer",
                    metadata={
                        "type": "answer",
                        "question": question,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            except Exception as e:
                print(f"Warning: Failed to archive to Mnemosyne: {e}")

        return response

    def get_memory_stats(self) -> Dict[str, any]:
        """Get statistics about stored memories."""
        if not self.memory:
            return {"error": "Mnemosyne not available"}

        try:
            stats = self.memory.get_stats()
            return stats
        except Exception as e:
            return {"error": str(e)}

    def search_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """Search archived conversations.

        Args:
            query: Search query (empty string returns most recent)
            limit: Maximum results

        Returns:
            List of memory entries
        """
        if not self.memory:
            return []

        try:
            # If query is empty, search for common terms to get recent memories
            search_query = query if query.strip() else "question answer variable code"

            results = self.memory.recall(
                query=search_query,
                top_k=limit
                # No session_id filter = team-wide
            )

            # If still no results, try getting all memories via get_context
            if not results:
                try:
                    context = self.memory.get_context(limit=limit)
                    # Convert context to list format
                    if isinstance(context, list):
                        return context
                except:
                    pass

            return results
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def archive_message(self, message: str, message_type: str = "manual") -> bool:
        """Archive a manual message to team memory.

        This allows manual typed messages to be stored in the hive mind
        so all engineers can see them.

        Args:
            message: The message content
            message_type: Type of message (manual, code, question, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.memory:
            return False

        try:
            self.memory.remember(
                content=message,
                importance=0.7,  # Manual messages are important
                source=f"{message_type}-message",
                metadata={
                    "type": message_type,
                    "engineer_id": self.engineer_id,
                    "team_id": self.team_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Archive failed: {e}")
            return False


def create_mnemosyne_agent(
    team_id: str,
    engineer_id: str,
    team_name: str = "Team"
) -> Optional[MnemosyneAIAgent]:
    """Create Mnemosyne-backed AI agent if credentials available.

    Returns:
        MnemosyneAIAgent instance or None if credentials not available
    """
    try:
        return MnemosyneAIAgent(
            team_id=team_id,
            engineer_id=engineer_id,
            team_name=team_name
        )
    except ValueError as e:
        print(f"Cannot create AI agent: {e}")
        return None
