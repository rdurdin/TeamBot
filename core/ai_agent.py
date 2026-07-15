"""AI Agent for answering questions with context from team knowledge."""

import os
import json
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class AIResponse:
    """AI-generated response."""
    answer: str
    sources: List[str]  # QA IDs used as context
    confidence: str  # "high", "medium", "low"


class AIAgent:
    """AI agent that answers questions using team knowledge as context."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5"):
        """Initialize AI agent.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-5)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError(
                "No API key provided. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )

    def answer_question(
        self,
        question: str,
        context_qa: List[dict],
        team_name: str,
    ) -> AIResponse:
        """Generate an answer using AI with team Q&A as context.

        Args:
            question: The question to answer
            context_qa: List of relevant Q&A entries for context
            team_name: Name of the team

        Returns:
            AIResponse with answer, sources, and confidence
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            )

        client = Anthropic(api_key=self.api_key)

        # Build context from previous Q&A
        context_text = self._build_context(context_qa)

        # Create prompt
        system_prompt = f"""You are TeamAgent, an AI assistant helping the {team_name} engineering team.

Your role:
- Answer technical questions based on the team's past Q&A history
- If the team has answered similar questions before, use that knowledge
- If you don't have enough context, say so clearly
- Always cite which past Q&A entries you're referencing
- Be concise and practical

Team Knowledge Base:
{context_text}"""

        user_prompt = f"Question: {question}"

        # Call Claude API
        message = client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        answer = message.content[0].text

        # Extract sources (simple heuristic - look for QA IDs mentioned)
        sources = self._extract_sources(answer, context_qa)

        # Determine confidence based on context availability
        confidence = "high" if len(context_qa) >= 2 else "medium" if len(context_qa) == 1 else "low"

        return AIResponse(
            answer=answer,
            sources=sources,
            confidence=confidence
        )

    def _build_context(self, qa_entries: List[dict]) -> str:
        """Build context text from Q&A entries."""
        if not qa_entries:
            return "No previous team knowledge available."

        context_parts = []
        for i, qa in enumerate(qa_entries[:5], 1):  # Limit to top 5
            qa_text = f"Q{i} (ID: {qa['id'][:8]}): {qa['question']}"
            if qa.get('answer'):
                qa_text += f"\nA{i}: {qa['answer']}"
            context_parts.append(qa_text)

        return "\n\n".join(context_parts)

    def _extract_sources(self, answer: str, context_qa: List[dict]) -> List[str]:
        """Extract which QA IDs were likely used as sources."""
        sources = []
        for qa in context_qa:
            qa_id_short = qa['id'][:8]
            # Check if the QA ID or question appears in the answer
            if qa_id_short in answer or qa['question'][:30] in answer:
                sources.append(qa['id'])
        return sources


def create_default_agent() -> Optional[AIAgent]:
    """Create AI agent with default settings if API key is available.

    Returns:
        AIAgent instance or None if no API key available
    """
    try:
        return AIAgent()
    except ValueError:
        return None
