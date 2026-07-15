"""Enhanced AI agent with Red Hat Claude API + Memory + Cases."""

import os
import json
import requests
import sys
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_manager import create_memory_manager
from integrations.rhcase_client import create_rhcase_client


@dataclass
class EnhancedResponse:
    """Enhanced AI response with memory and case context."""
    answer: str
    sources: List[str]
    confidence: str
    memory_used: bool
    cases_referenced: List[str]
    kcs_articles: List[str]


class RedHatEnhancedAgent:
    """Enhanced AI agent using Red Hat Claude API with memory and case integration."""

    def __init__(
        self,
        team_id: str,
        engineer_id: str,
        team_name: str,
        api_url: Optional[str] = None,
        user_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize enhanced agent."""
        self.team_id = team_id
        self.engineer_id = engineer_id
        self.team_name = team_name
        self.api_url = api_url or os.environ.get("MODEL_API")
        self.user_key = user_key or os.environ.get("USER_KEY")
        self.model = model or os.environ.get("MODEL_ID", "claude-sonnet-4-6")

        if not self.api_url or not self.user_key:
            raise ValueError("No Red Hat credentials found")

        # Initialize memory
        self.memory = create_memory_manager(team_id, engineer_id, team_name)

        # Initialize rhcase
        self.rhcase = create_rhcase_client()

    def answer_with_context(
        self,
        question: str,
        context_qa: List[Dict],
        case_number: Optional[str] = None,
        remember: bool = True
    ) -> EnhancedResponse:
        """Answer with full context from memory, Q&A, and cases."""

        # Gather all context
        context_parts = []
        memory_used = False
        cases_referenced = []
        kcs_articles = []

        # 1. Team Q&A
        if context_qa:
            qa_context = self._format_qa_context(context_qa)
            context_parts.append(f"## Team Q&A History\n{qa_context}")

        # 2. Memory
        if self.memory:
            try:
                memory_context = self.memory.get_conversation_context(query=question, limit=10)
                if memory_context and memory_context != "No prior context available.":
                    context_parts.append(f"## Team Memory\n{memory_context}")
                    memory_used = True
            except Exception:
                pass

        # 3. Case context - check memory first, don't fetch from network
        if case_number:
            if self.memory:
                try:
                    case_memories = self.memory.recall_case_context(case_number, top_k=10)
                    if case_memories:
                        case_mem = "\n".join([f"- {m.get('content', str(m))}" for m in case_memories])
                        context_parts.append(f"## Case {case_number} Context\n{case_mem}")
                        cases_referenced.append(case_number)
                        memory_used = True
                except Exception:
                    pass

        # 4. KCS search - DISABLED (requires network/credentials)
        # if self.rhcase and any(word in question.lower() for word in ['how', 'error', 'issue', 'problem', 'fix']):
        #     try:
        #         articles = self.rhcase.search_kcs(question, limit=3)
        #         if articles:
        #             kcs_text = "\n".join([f"- {a.title} ({a.id})" for a in articles])
        #             context_parts.append(f"## KCS Articles\n{kcs_text}")
        #             kcs_articles = [a.id for a in articles]
        #     except Exception:
        #         pass

        # Build prompt
        full_context = "\n\n".join(context_parts) if context_parts else "No context available."

        system_prompt = f"""You are TeamAgent helping {self.team_name} with Red Hat support.

You have:
- Team Q&A history
- Persistent memory (Mnemosyne BEAM)
- Red Hat case data
- KCS knowledge base

Context:
{full_context}"""

        # Call Red Hat Claude API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.user_key}"
        }

        payload = {
            "anthropic_version": "vertex-2023-10-16",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": f"{system_prompt}\n\nQuestion: {question}"}]
                }
            ],
            "max_tokens": 3000,
            "temperature": 0
        }

        url = f"{self.api_url}/sonnet/models/{self.model}:streamRawPredict"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "content" in data and len(data["content"]) > 0:
                answer = data["content"][0].get("text", "No response")
            else:
                answer = "No response generated"

        except Exception as e:
            raise Exception(f"API call failed: {e}")

        # Extract sources
        sources = self._extract_sources(answer, context_qa, cases_referenced, kcs_articles)

        # Confidence
        confidence = self._determine_confidence(
            has_qa=len(context_qa) > 0,
            has_memory=memory_used,
            has_case=len(cases_referenced) > 0,
            has_kcs=len(kcs_articles) > 0
        )

        # Remember interaction
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
        """Format Q&A as context."""
        parts = []
        for i, qa in enumerate(qa_entries[:5], 1):
            text = f"Q{i}: {qa['question']}"
            if qa.get('answer'):
                text += f"\nA{i}: {qa['answer'][:300]}"
            parts.append(text)
        return "\n\n".join(parts)

    def _extract_sources(self, answer: str, context_qa: List[Dict], cases: List[str], kcs: List[str]) -> List[str]:
        """Extract sources from answer."""
        sources = []
        for qa in context_qa:
            if qa['id'][:8] in answer:
                sources.append(f"qa:{qa['id'][:8]}")
        for case in cases:
            if case in answer:
                sources.append(f"case:{case}")
        for article in kcs:
            if article in answer:
                sources.append(f"kcs:{article}")
        return sources

    def _determine_confidence(self, has_qa: bool, has_memory: bool, has_case: bool, has_kcs: bool) -> str:
        """Determine confidence level."""
        score = sum([has_qa, has_memory, has_case, has_kcs])
        if score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        elif score >= 1:
            return "low"
        else:
            return "minimal"


def create_redhat_enhanced_agent(team_id: str, engineer_id: str, team_name: str) -> Optional[RedHatEnhancedAgent]:
    """Create enhanced agent if credentials available."""
    try:
        return RedHatEnhancedAgent(team_id, engineer_id, team_name)
    except ValueError:
        return None
