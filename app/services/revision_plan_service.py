"""Orchestrates revision plan generation via OpenAI."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.revision_plan_prompt import build_revision_plan_messages
from app.schemas.revision_plan_schema import GenerateRevisionPlanRequest, GenerateRevisionPlanResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


def _coerce_response(raw: dict[str, Any], request: GenerateRevisionPlanRequest) -> GenerateRevisionPlanResponse:
    """Merge model output with safe fallbacks."""
    data = dict(raw)
    data.setdefault("success", True)
    if not isinstance(data.get("weak_topics"), list) or not data["weak_topics"]:
        data["weak_topics"] = list(request.weak_topics)

    try:
        return GenerateRevisionPlanResponse.model_validate(data)
    except ValidationError as e:
        logger.warning("Revision plan response validation failed, using minimal safe shape: %s", e)
        return GenerateRevisionPlanResponse(
            success=True,
            risk_level=str(data.get("risk_level") or "medium"),
            summary=str(data.get("summary") or "Focus on the listed weak topics with steady practice."),
            weak_topics=list(request.weak_topics),
            revision_notes=[],
            flashcards=[],
            practice_questions=[],
            study_plan=[],
            recommended_actions=["Review weak topics and retry similar practice questions."],
        )


class RevisionPlanService:
    def __init__(self) -> None:
        self._openai = OpenAIService()

    @property
    def is_configured(self) -> bool:
        return self._openai.is_configured

    async def generate(self, body: GenerateRevisionPlanRequest) -> GenerateRevisionPlanResponse:
        messages = build_revision_plan_messages(body)
        raw = await self._openai.complete_json(messages, temperature=0.25)
        if not isinstance(raw, dict):
            raise ValueError("Model output must be a JSON object.")
        return _coerce_response(raw, body)
