"""Institutional analytics generation."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.analytics_prompt import build_analytics_messages
from app.schemas.analytics_schema import AnalyzeAcademicIntelligenceRequest, AnalyzeAcademicIntelligenceResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


def _coerce(raw: dict[str, Any]) -> AnalyzeAcademicIntelligenceResponse:
    data = dict(raw)
    data.setdefault("success", True)
    for key in (
        "at_risk_students",
        "weak_topics",
        "performance_clusters",
        "interventions",
        "summary",
        "department_insights",
        "cohort_trends",
    ):
        if not isinstance(data.get(key), list):
            data[key] = []
    try:
        return AnalyzeAcademicIntelligenceResponse.model_validate(data)
    except ValidationError as e:
        logger.warning("Analytics validation failed: %s", e)
        return AnalyzeAcademicIntelligenceResponse(
            success=True,
            course_health_score=55,
            at_risk_students=[],
            weak_topics=[],
            performance_clusters=[],
            interventions=["Increase formative checkpoints", "Offer targeted revision workshops"],
            summary=["Analytics model returned partial data; rerun when the cohort dataset is richer."],
            department_insights=["Continue monitoring engagement alongside scores."],
            cohort_trends=["Performance spread suggests differentiated support."],
        )


class AnalyticsIntelligenceService:
    def __init__(self) -> None:
        self._openai = OpenAIService()

    @property
    def is_configured(self) -> bool:
        return self._openai.is_configured

    async def analyze(self, body: AnalyzeAcademicIntelligenceRequest) -> AnalyzeAcademicIntelligenceResponse:
        messages = build_analytics_messages(body)
        raw = await self._openai.complete_json(messages, temperature=0.26)
        if not isinstance(raw, dict):
            raise ValueError("Model output must be a JSON object.")
        return _coerce(raw)
