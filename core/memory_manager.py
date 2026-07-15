"""Memory manager using Mnemosyne BEAM for persistent memory."""

import os
from typing import Optional, List, Dict
from pathlib import Path


class MemoryManager:
    """Manages team memory using Mnemosyne BEAM architecture."""

    def __init__(self, team_id: str, engineer_id: str, team_name: str):
        """Initialize memory manager.

        Args:
            team_id: Team ID
            engineer_id: Current engineer ID
            team_name: Team name for memory bank
        """
        self.team_id = team_id
        self.engineer_id = engineer_id
        self.team_name = team_name
        self._memory = None
        self._shared_memory = None

    def _get_memory(self):
        """Get or create team-scoped Mnemosyne instance."""
        if self._memory:
            return self._memory

        try:
            from mnemosyne import Mnemosyne
            from mnemosyne.core.banks import BankManager
        except ImportError:
            raise ImportError(
                "Mnemosyne not installed. Install with: pip install mnemosyne-memory"
            )

        # Create memory bank if it doesn't exist
        bank_name = f"team-{self.team_name.lower().replace(' ', '-')}"

        try:
            BankManager.create_bank(bank_name)
        except Exception:
            # Bank already exists, that's fine
            pass

        # Create team-scoped memory with author tracking
        self._memory = Mnemosyne(
            bank=bank_name,
            author_id=self.engineer_id,
            author_type="engineer",
            channel_id=self.team_id,  # Team ID as channel
        )

        return self._memory

    def _get_shared_memory(self):
        """Get shared memory for cross-team knowledge."""
        if self._shared_memory:
            return self._shared_memory

        try:
            from mnemosyne import Mnemosyne
        except ImportError:
            raise ImportError("Mnemosyne not installed")

        # Shared memory bank for system-wide knowledge
        self._shared_memory = Mnemosyne(
            bank="teamagent-shared",
            author_id=self.engineer_id,
            author_type="engineer",
        )

        return self._shared_memory

    def remember(self, content: str, importance: float = 0.7, source: str = "conversation"):
        """Store a memory in team memory.

        Args:
            content: What to remember
            importance: Importance score 0-1
            source: Source of the memory
        """
        memory = self._get_memory()
        memory.remember(content, importance=importance, source=source)

    def recall(self, query: str, top_k: int = 5) -> List[Dict]:
        """Recall relevant memories.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of memory dictionaries
        """
        memory = self._get_memory()
        results = memory.recall(query, top_k=top_k)
        return results

    def remember_case_context(self, case_number: str, context: str, importance: float = 0.8):
        """Remember context about a Red Hat support case.

        Args:
            case_number: Case number
            context: Context about the case
            importance: Importance score
        """
        content = f"Case {case_number}: {context}"
        self.remember(content, importance=importance, source=f"case-{case_number}")

    def recall_case_context(self, case_number: str, top_k: int = 10) -> List[Dict]:
        """Recall memories related to a case.

        Args:
            case_number: Case number
            top_k: Number of results

        Returns:
            List of relevant memories
        """
        query = f"Case {case_number}"
        return self.recall(query, top_k=top_k)

    def remember_qa(self, question: str, answer: str, qa_id: str):
        """Remember a Q&A exchange.

        Args:
            question: The question
            answer: The answer
            qa_id: Q&A entry ID for reference
        """
        content = f"Q: {question}\nA: {answer}"
        self.remember(content, importance=0.75, source=f"qa-{qa_id}")

    def get_conversation_context(self, query: str = None, limit: int = 10) -> str:
        """Get recent conversation context for AI.

        Args:
            query: Optional query to filter context
            limit: Max memories to retrieve

        Returns:
            Formatted context string for AI
        """
        # Always use recall to get memories
        if query:
            memories = self.recall(query, top_k=limit)
        else:
            # Get all recent memories
            memories = self.recall("", top_k=limit)

        if not memories:
            return "No prior context available."

        # Format memories as context
        context_parts = []
        for i, mem in enumerate(memories, 1):
            if isinstance(mem, dict):
                content = mem.get('content', str(mem))
            else:
                content = str(mem)
            context_parts.append(f"{i}. {content}")

        return "\n".join(context_parts)

    def consolidate(self):
        """Trigger memory consolidation (working → episodic)."""
        try:
            memory = self._get_memory()
            # Call sleep/consolidation if available
            if hasattr(memory, 'sleep'):
                memory.sleep()
        except Exception as e:
            # Consolidation not critical, just log
            pass

    def get_stats(self) -> Dict:
        """Get memory statistics.

        Returns:
            Dictionary with memory stats
        """
        try:
            memory = self._get_memory()
            if hasattr(memory, 'stats'):
                return memory.stats()
            return {"status": "available"}
        except:
            return {"status": "unavailable"}


def create_memory_manager(team_id: str, engineer_id: str, team_name: str) -> Optional[MemoryManager]:
    """Create a memory manager if Mnemosyne is available.

    Args:
        team_id: Team ID
        engineer_id: Engineer ID
        team_name: Team name

    Returns:
        MemoryManager instance or None
    """
    try:
        return MemoryManager(team_id, engineer_id, team_name)
    except ImportError:
        return None
