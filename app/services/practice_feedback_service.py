"""Practice quiz post-submit AI feedback."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.practice_feedback_prompt import build_practice_feedback_messages
from app.schemas.practice_feedback_schema import (
    GeneratePracticeFeedbackRequest,
    GeneratePracticeFeedbackResponse,
)
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


def _coerce_response(raw: dict[str, Any], request: GeneratePracticeFeedbackRequest) -> GeneratePracticeFeedbackResponse:
    data = dict(raw)
    if not isinstance(data.get("recommended_topics"), list) or not data["recommended_topics"]:
        data["recommended_topics"] = list(request.weak_topics)[:6]

    try:
        return GeneratePracticeFeedbackResponse.model_validate(data)
    except ValidationError as e:
        logger.warning("Practice feedback validation failed, using safe defaults: %s", e)
        return GeneratePracticeFeedbackResponse(
            summary="Keep practicing the topics you found difficult; small daily sessions add up quickly.",
            recommended_topics=list(request.weak_topics)[:6],
            revision_tips=[
                "Rewrite key definitions in your own words.",
                "Work three similar problems without looking at notes, then check answers.",
            ],
            recommended_quizzes=[t for t in request.available_quiz_titles[:3]],
            motivation_message="You are building real skill—stay curious and keep going.",
        )


class PracticeFeedbackService:
    def __init__(self) -> None:
        self._openai = OpenAIService()

    @property
    def is_configured(self) -> bool:
        return self._openai.is_configured

    async def generate(self, body: GeneratePracticeFeedbackRequest) -> GeneratePracticeFeedbackResponse:
        messages = build_practice_feedback_messages(body)
        raw = await self._openai.complete_json(messages, temperature=0.35)
        if not isinstance(raw, dict):
            raise ValueError("Model output must be a JSON object.")
        return _coerce_response(raw, body)
