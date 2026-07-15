"""AI agent using Red Hat's internal Claude endpoint."""

import os
import json
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
import urllib3

# Disable SSL warnings for internal Red Hat certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class AIResponse:
    """AI-generated response."""
    answer: str
    sources: List[str]
    confidence: str


class RedHatAIAgent:
    """AI agent using Red Hat's internal Claude API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        user_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize Red Hat AI agent.

        Args:
            api_url: Red Hat Claude API URL (defaults to MODEL_API env var)
            user_key: User key for authentication (defaults to USER_KEY env var)
            model: Model ID (defaults to MODEL_ID env var)
        """
        self.api_url = api_url or os.environ.get("MODEL_API")
        self.user_key = user_key or os.environ.get("USER_KEY")
        self.model = model or os.environ.get("MODEL_ID", "claude-sonnet-4-6")

        if not self.api_url:
            raise ValueError("No MODEL_API found. Set: export MODEL_API='your-endpoint'")
        if not self.user_key:
            raise ValueError("No USER_KEY found. Set: export USER_KEY='your-key'")

    def answer_question(
        self,
        question: str,
        context_qa: List[dict],
        team_name: str,
        memory_context: str = "",
    ) -> AIResponse:
        """Generate an answer using Red Hat's Claude API.

        Args:
            question: The question to answer
            context_qa: List of relevant Q&A entries for context
            team_name: Name of the team

        Returns:
            AIResponse with answer, sources, and confidence
        """
        # Build context from previous Q&A
        context_text = self._build_context(context_qa)

        # Add memory context if available
        full_context = context_text
        if memory_context:
            full_context = f"{context_text}\n\n## Team Memory (Past Discussions):\n{memory_context}"

        # Create system prompt
        system_prompt = f"""You are TeamAgent, an AI assistant helping the {team_name} engineering team.

Your role:
- Answer technical questions based on the team's past Q&A history AND memory
- Reference specific past discussions when relevant
- If you don't have enough context, say so clearly
- Be concise and practical

Team Knowledge Base:
{full_context}"""

        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.user_key}"  # Red Hat API Gateway requires Bearer token
        }

        payload = {
            "anthropic_version": "vertex-2023-10-16",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": f"{system_prompt}\n\nQuestion: {question}"}]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0
        }

        # Make API call with user_key as query parameter AND Authorization header
        url = f"{self.api_url}/sonnet/models/{self.model}:streamRawPredict?user_key={self.user_key}"

        try:
            # Disable SSL verification for internal Red Hat certificates
            response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract answer from response
            if "content" in data and len(data["content"]) > 0:
                answer = data["content"][0].get("text", "No response generated")
            else:
                answer = "No response generated"

        except requests.exceptions.RequestException as e:
            raise Exception(f"API call failed: {e}")

        # Extract sources
        sources = self._extract_sources(answer, context_qa)

        # Determine confidence
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
        for i, qa in enumerate(qa_entries[:5], 1):
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
            if qa_id_short in answer or qa['question'][:30] in answer:
                sources.append(qa['id'])
        return sources


def create_redhat_agent() -> Optional[RedHatAIAgent]:
    """Create Red Hat AI agent with default settings if credentials available.

    Returns:
        RedHatAIAgent instance or None if credentials not available
    """
    try:
        return RedHatAIAgent()
    except ValueError:
        return None
