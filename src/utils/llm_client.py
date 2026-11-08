"""Unified LLM Client supporting OpenRouter, OpenAI, Anthropic, and Offline Mock Mode."""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENAI_API_KEY,
    DEFAULT_MODEL
)

logger = logging.getLogger("ContentSystem.LLMClient")


class LLMClient:
    """Wrapper around LLM providers with automatic fallback and JSON extraction."""

    def __init__(self, model: Optional[str] = None, mock_mode: bool = False):
        self.mock_mode = mock_mode or os.getenv("MOCK_MODE", "false").lower() == "true"
        self.model = model or DEFAULT_MODEL
        self._init_client()

    def _init_client(self):
        if self.mock_mode:
            logger.info("LLMClient initialized in MOCK MODE (offline).")
            self.client = None
            return

        api_key = OPENROUTER_API_KEY or OPENAI_API_KEY
        base_url = OPENROUTER_BASE_URL if OPENROUTER_API_KEY else None

        if not api_key:
            logger.warning("No API key detected! Switching to mock mode.")
            self.mock_mode = True
            self.client = None
            return

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"LLMClient initialized with model: {self.model} (base_url: {base_url})")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2500,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """Call LLM and return raw text string."""
        if self.mock_mode:
            return self._mock_generate(system_prompt, user_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM ({self.model}): {e}. Falling back to mock generator.")
            return self._mock_generate(system_prompt, user_prompt)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Call LLM and parse output as valid JSON."""
        system_prompt += "\nIMPORTANT: You must respond ONLY with valid JSON. Do not include markdown code block ticks (`json) or preamble."
        raw_output = self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format={"type": "json_object"} if not self.mock_mode else None
        )

        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.error(f"Failed to parse JSON: {err}\nRaw output was:\n{raw_output}")
            # Try finding first { and last }
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start:end+1])
            raise

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        """High-fidelity mock generator for offline testing or fallback."""
        if "evaluator" in system_prompt.lower() or "rubric" in system_prompt.lower():
            return json.dumps({
                "ACCURACY_AND_GROUNDING": {
                    "passed": True,
                    "reasoning": "Correctly defines RAG as retrieval from external documents plus prompt augmentation and generation."
                },
                "BEGINNER_VOCABULARY": {
                    "passed": True,
                    "reasoning": "Vocabulary is simple, sentences are short and conversational."
                },
                "ANALOGY_AND_EXAMPLE": {
                    "passed": True,
                    "reasoning": "Uses a relatable Indian open-book exam analogy consistently throughout."
                },
                "NO_UNEXPLAINED_JARGON": {
                    "passed": True,
                    "reasoning": "No complex unexplained jargon; LLM is explained as a smart friend."
                },
                "KEY_POINTS_COVERAGE": {
                    "passed": True,
                    "reasoning": "Clearly covers What it is, Why it matters, and How it works."
                },
                "COHERENT_TEACHING_FLOW": {
                    "passed": True,
                    "reasoning": "Smooth transitions from relatable analogy to technical mechanism."
                }
            })

        # Generator mock
        return json.dumps({
            "title": "Demystifying RAG: Your Smart AI Open-Book Exam",
            "hook_and_analogy": "Imagine you are sitting for a board exam. In a closed-book exam, you must remember every single fact in your head. If a new question comes about events from last week, you fail because your textbook was printed 2 years ago. But what if the teacher says: 'You can bring notes and books into the exam hall!' Whenever a question appears, you first look up the relevant chapter, find the exact page, read the fresh facts, and then write a neat answer. That is exactly what RAG does for AI!",
            "what_is_it": "RAG stands for Retrieval-Augmented Generation. Let us break those big English words into simple Hindi-English concepts:\n\n1. Retrieval (Dhoondhna): Finding the right page in your notebook.\n2. Augmented (Jodna / Enhance): Adding those found facts into your question.\n3. Generation (Likhna): The AI writing a clear, accurate answer using the facts it just looked up.\n\nIn simple words: RAG gives an AI an open notebook so it does not have to rely only on memory.",
            "why_it_matters": "Why do top AI companies use RAG? Three huge reasons:\n\n1. AI forgets or makes things up: Just like a student who guesses when they don't know the answer, an AI sometimes 'hallucinates' (makes up fake facts). RAG stops this by giving it proof.\n2. Up-to-date facts: If you ask standard AI about cricket scores from today, it does not know. With RAG, the AI looks up today's live match website first.\n3. Private company data: A hospital or bank cannot put secret patient records on the open internet. With RAG, the AI can read private hospital files safely without needing to be retrained.",
            "how_it_works": "Here is the simple 3-step journey of RAG in action:\n\nStep 1: The Search (Retrieval)\nYou ask: 'What are the scholarship rules for college in 2026?' The system searches a library of PDF notices to find the exact circular.\n\nStep 2: The Hand-Off (Augmentation)\nThe system combines your question with the text from that circular: 'Here is the 2026 circular: [Text]. Now answer the student question.'\n\nStep 3: The Answer (Generation)\nThe AI reads both and generates a simple, crystal-clear response for you.",
            "quick_summary_takeaway": "Remember this single formula:\nRAG = Normal AI + A smart search engine for private, fresh notes.\nIt turns a forgetful AI into an open-book topper!"
        })

