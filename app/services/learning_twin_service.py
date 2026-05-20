"""Learning twin generation."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.learning_twin_prompt import build_learning_twin_messages
from app.schemas.learning_twin_schema import GenerateLearningTwinRequest, GenerateLearningTwinResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


def _coerce(raw: dict[str, Any]) -> GenerateLearningTwinResponse:
    data = dict(raw)
    data.setdefault("success", True)
    try:
        return GenerateLearningTwinResponse.model_validate(data)
    except ValidationError as e:
        logger.warning("Learning twin validation failed: %s", e)
        return GenerateLearningTwinResponse(
            success=True,
            academic_health_score=int(data.get("academic_health_score") or 50),
            risk_level=str(data.get("risk_level") or "medium"),
            predicted_next_score=int(data.get("predicted_next_score") or 50),
            strengths=["Consistent effort where data is available"],
            weaknesses=["Insufficient data for fine-grained diagnosis"],
            learning_pattern="Continue structured revision and seek feedback from your lecturer.",
            recommended_actions=["Review recent assessments", "Clarify difficult topics in office hours"],
            revision_focus=["Core concepts from recent attempts"],
            lecturer_intervention="Offer a short check-in to align expectations and study habits.",
        )


class LearningTwinService:
    def __init__(self) -> None:
        self._openai = OpenAIService()

    @property
    def is_configured(self) -> bool:
        return self._openai.is_configured

    async def generate(self, body: GenerateLearningTwinRequest) -> GenerateLearningTwinResponse:
        messages = build_learning_twin_messages(body)
        raw = await self._openai.complete_json(messages, temperature=0.28)
        if not isinstance(raw, dict):
            raise ValueError("Model output must be a JSON object.")
        return _coerce(raw)
