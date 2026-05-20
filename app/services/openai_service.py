"""Reusable OpenAI client wrapper for all AI endpoints."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import APIError, AsyncOpenAI, RateLimitError
from openai.types.chat import ChatCompletion

from app.config.settings import settings
from app.schemas.question_schema import GeneratedQuestion, GenerateQuestionsRequest

logger = logging.getLogger(__name__)


def _expected_question_types(payload: GenerateQuestionsRequest) -> list[str]:
    n = payload.number_of_questions
    base = list(payload.question_types) if payload.question_types else [payload.question_type]
    return [base[(payload.question_type_offset + i) % len(base)] for i in range(n)]


class OpenAIService:
    """Thin async service — extend with mark_answer, fairness analysis, etc."""

    def __init__(self) -> None:
        self._model = settings.openai_model
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def complete_json(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.35,
    ) -> dict[str, Any]:
        """Call Chat Completions with JSON mode and parse the assistant message as JSON."""
        if not self._client:
            raise ValueError("OPENAI_API_KEY is not set; cannot call OpenAI.")

        try:
            completion: ChatCompletion = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except RateLimitError as e:
            logger.warning("OpenAI rate limit: %s", e)
            raise
        except APIError as e:
            logger.exception("OpenAI API error: %s", e)
            raise

        choice = completion.choices[0].message
        raw = (choice.content or "").strip()
        if not raw:
            raise ValueError("OpenAI returned an empty message body.")

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON from model: %s", raw[:500])
            raise ValueError("Model output was not valid JSON.") from e

    async def generate_questions_json(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Call Chat Completions with JSON mode and parse the assistant message as JSON."""
        return await self.complete_json(messages, temperature=0.35)

    async def generate_questions(
        self,
        payload: GenerateQuestionsRequest,
        messages: list[dict[str, Any]],
    ) -> list[GeneratedQuestion]:
        data = await self.generate_questions_json(messages)
        items = data.get("questions")
        if not isinstance(items, list):
            raise ValueError("JSON must contain a 'questions' array.")

        expected_types = _expected_question_types(payload)
        out: list[GeneratedQuestion] = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"questions[{i}] must be an object.")
            merged = dict(item)
            if merged.get("question_type") != expected_types[i]:
                merged["question_type"] = expected_types[i]
            out.append(GeneratedQuestion.model_validate(merged))

        if len(out) != payload.number_of_questions:
            logger.warning(
                "Expected %s questions, got %s — accepting returned count.",
                payload.number_of_questions,
                len(out),
            )
        return out
