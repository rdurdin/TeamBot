"""AI agent using Google Gemini API."""

import os
import json
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class AIResponse:
    """AI-generated response."""
    answer: str
    sources: List[str]
    confidence: str


class RedHatAIAgent:
    """AI agent using Google Gemini API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        user_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = user_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("MODEL_ID", "gemini-2.0-flash")

        if not self.api_key:
            raise ValueError("No GEMINI_API_KEY found. Set: export GEMINI_API_KEY='your-key'")

    def answer_question(
        self,
        question: str,
        context_qa: List[dict],
        team_name: str,
        memory_context: str = "",
    ) -> AIResponse:
        context_text = self._build_context(context_qa)

        full_context = context_text
        if memory_context:
            full_context = f"{context_text}\n\n## Team Memory (Past Discussions):\n{memory_context}"

        system_prompt = f"""You are TeamAgent, an AI assistant helping the {team_name} engineering team.

Your role:
- Answer technical questions based on the team's past Q&A history AND memory
- Reference specific past discussions when relevant
- If you don't have enough context, say so clearly
- Be concise and practical

Team Knowledge Base:
{full_context}"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": question}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 2000,
                "temperature": 0
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                answer = parts[0].get("text", "No response generated") if parts else "No response generated"
            else:
                answer = "No response generated"

        except requests.exceptions.RequestException as e:
            raise Exception(f"API call failed: {e}")

        sources = self._extract_sources(answer, context_qa)
        confidence = "high" if len(context_qa) >= 2 else "medium" if len(context_qa) == 1 else "low"

        return AIResponse(
            answer=answer,
            sources=sources,
            confidence=confidence
        )

    def _build_context(self, qa_entries: List[dict]) -> str:
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
        sources = []
        for qa in context_qa:
            qa_id_short = qa['id'][:8]
            if qa_id_short in answer or qa['question'][:30] in answer:
                sources.append(qa['id'])
        return sources


def create_redhat_agent() -> Optional[RedHatAIAgent]:
    try:
        return RedHatAIAgent()
    except ValueError:
        return None
