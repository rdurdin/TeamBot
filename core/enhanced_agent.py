"""Enhanced AI agent with persistent memory and Red Hat case integration."""

import os
from typing import Optional, List, Dict
from dataclasses import dataclass

from .ai_agent import AIResponse


@dataclass
class EnhancedResponse:
    """Enhanced AI response with memory and case context."""
    answer: str
    sources: List[str]  # QA IDs, case numbers, KCS article IDs
    confidence: str
    memory_used: bool
    cases_referenced: List[str]
    kcs_articles: List[str]


class EnhancedAIAgent:
    """AI agent with persistent memory and Red Hat case integration."""

    def __init__(
        self,
        team_id: str,
        engineer_id: str,
        team_name: str,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5"
    ):
        """Initialize enhanced AI agent.

        Args:
            team_id: Team ID
            engineer_id: Engineer ID
            team_name: Team name
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.team_id = team_id
        self.engineer_id = engineer_id
        self.team_name = team_name
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("No ANTHROPIC_API_KEY found")

        # Initialize memory manager
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from core.memory_manager import create_memory_manager
        self.memory = create_memory_manager(team_id, engineer_id, team_name)

        # Initialize rhcase client
        from integrations.rhcase_client import create_rhcase_client
        self.rhcase = create_rhcase_client()

    def answer_with_context(
        self,
        question: str,
        context_qa: List[Dict],
        case_number: Optional[str] = None,
        remember: bool = True
    ) -> EnhancedResponse:
        """Answer a question using all available context.

        Args:
            question: The question
            context_qa: Q&A context from archive
            case_number: Optional case number for case-specific context
            remember: Whether to remember this interaction

        Returns:
            EnhancedResponse with answer and metadata
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic")

        client = Anthropic(api_key=self.api_key)

        # Gather all context
        context_parts = []
        memory_used = False
        cases_referenced = []
        kcs_articles = []

        # 1. Team Q&A history
        if context_qa:
            qa_context = self._format_qa_context(context_qa)
            context_parts.append(f"## Team Q&A History\n{qa_context}")

        # 2. Memory context
        if self.memory:
            try:
                memory_context = self.memory.get_conversation_context(query=question, limit=10)
                if memory_context and memory_context != "No prior context available.":
                    context_parts.append(f"## Team Memory (Past Discussions)\n{memory_context}")
                    memory_used = True
            except Exception as e:
                # Memory fetch failed, continue without it
                pass

        # 3. Case-specific context
        if case_number and self.rhcase:
            try:
                case_summary = self.rhcase.get_case_summary(case_number)
                context_parts.append(f"## Red Hat Support Case\n{case_summary}")
                cases_referenced.append(case_number)

                # Get case memory
                if self.memory:
                    case_memories = self.memory.recall_case_context(case_number, top_k=5)
                    if case_memories:
                        case_mem_text = "\n".join([
                            f"- {m.get('content', str(m))}" for m in case_memories
                        ])
                        context_parts.append(f"## Case {case_number} History\n{case_mem_text}")
                        memory_used = True

            except Exception:
                pass

        # 4. Search KCS if question looks like a problem
        if self.rhcase and any(word in question.lower() for word in ['how', 'error', 'issue', 'problem', 'fix']):
            try:
                articles = self.rhcase.search_kcs(question, limit=3)
                if articles:
                    kcs_text = "\n".join([
                        f"- {a.title} ({a.id}): {a.url}"
                        for a in articles
                    ])
                    context_parts.append(f"## Relevant KCS Articles\n{kcs_text}")
                    kcs_articles = [a.id for a in articles]
            except Exception:
                pass

        # Build system prompt
        full_context = "\n\n".join(context_parts) if context_parts else "No prior context available."

        system_prompt = f"""You are TeamAgent, an AI assistant helping the {self.team_name} engineering team with Red Hat support cases and technical questions.

You have access to:
- Team's past Q&A discussions
- Persistent memory of past conversations (via Mnemosyne BEAM)
- Red Hat support case data
- KCS knowledge base articles

Use all available context to provide accurate, helpful answers. Always cite your sources.

Available Context:
{full_context}"""

        user_prompt = f"Question: {question}"

        # Call Claude
        message = client.messages.create(
            model=self.model,
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        answer = message.content[0].text

        # Extract sources
        sources = self._extract_sources(answer, context_qa, cases_referenced, kcs_articles)

        # Determine confidence
        confidence = self._determine_confidence(
            has_qa=len(context_qa) > 0,
            has_memory=memory_used,
            has_case=len(cases_referenced) > 0,
            has_kcs=len(kcs_articles) > 0
        )

        # Remember this interaction
        if remember and self.memory:
            try:
                self.memory.remember(
                    f"Q: {question}\nA: {answer[:500]}",
                    importance=0.8,
                    source="ai-conversation"
                )
                if case_number:
                    self.memory.remember_case_context(
                        case_number,
                        f"Discussed: {question[:200]}",
                        importance=0.7
                    )
            except Exception:
                pass

        return EnhancedResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            memory_used=memory_used,
            cases_referenced=cases_referenced,
            kcs_articles=kcs_articles
        )

    def _format_qa_context(self, qa_entries: List[Dict]) -> str:
        """Format Q&A entries as context."""
        parts = []
        for i, qa in enumerate(qa_entries[:5], 1):
            text = f"Q{i}: {qa['question']}"
            if qa.get('answer'):
                text += f"\nA{i}: {qa['answer'][:300]}"
            parts.append(text)
        return "\n\n".join(parts)

    def _extract_sources(
        self,
        answer: str,
        context_qa: List[Dict],
        cases: List[str],
        kcs: List[str]
    ) -> List[str]:
        """Extract sources mentioned in answer."""
        sources = []

        # Check QA IDs
        for qa in context_qa:
            if qa['id'][:8] in answer or qa['question'][:30] in answer:
                sources.append(f"qa:{qa['id'][:8]}")

        # Check case numbers
        for case in cases:
            if case in answer:
                sources.append(f"case:{case}")

        # Check KCS articles
        for article_id in kcs:
            if article_id in answer:
                sources.append(f"kcs:{article_id}")

        return sources

    def _determine_confidence(
        self,
        has_qa: bool,
        has_memory: bool,
        has_case: bool,
        has_kcs: bool
    ) -> str:
        """Determine confidence based on available context."""
        score = sum([has_qa, has_memory, has_case, has_kcs])

        if score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        elif score >= 1:
            return "low"
        else:
            return "minimal"
