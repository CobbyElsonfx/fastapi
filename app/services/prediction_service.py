"""Academic risk prediction — heuristics + LLM narrative."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.prediction_prompt import build_prediction_messages
from app.schemas.prediction_schema import (
    PredictAcademicRiskRequest,
    PredictAcademicRiskResponse,
    StudentRiskData,
)
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


def _clamp(v: float | int) -> float:
    return max(0.0, min(100.0, float(v)))


def compute_heuristic(student: StudentRiskData) -> dict[str, Any]:
    """Weighted composite (0-100) for failure pressure + suggested risk bands."""
    att = _clamp(student.attendance)
    qz = _clamp(student.quiz_average)
    asg = _clamp(student.assignment_average)
    eng = _clamp(student.engagement)
    fail_pen = min(100.0, float(student.previous_failures) * 12.0)
    miss_pen = min(100.0, float(student.missed_assessments) * 15.0)

    # Higher score => higher failure probability
    failure = (
        (100.0 - att) * 0.22
        + (100.0 - qz) * 0.22
        + (100.0 - asg) * 0.18
        + (100.0 - eng) * 0.13
        + fail_pen * 0.15
        + miss_pen * 0.10
    )
    failure = max(5.0, min(97.0, failure))

    def band(x: float) -> str:
        if x < 35:
            return "low"
        if x < 65:
            return "medium"
        return "high"

    dropout = band(failure * 0.9 + (100.0 - att) * 0.1)
    burnout = band((100.0 - eng) * 0.55 + (100.0 - qz) * 0.45)
    urgency = band(failure)

    return {
        "failure_probability": int(round(failure)),
        "dropout_risk_hint": dropout,
        "burnout_risk_hint": burnout,
        "intervention_urgency_hint": urgency,
    }


def _coerce(raw: dict[str, Any], heuristic: dict[str, Any]) -> PredictAcademicRiskResponse:
    data = dict(raw)
    data.setdefault("success", True)
    # Soft blend: keep AI narrative but nudge failure_probability toward heuristic if wildly off
    h_fp = int(heuristic["failure_probability"])
    try:
        ai_fp = int(data.get("failure_probability", h_fp))
    except (TypeError, ValueError):
        ai_fp = h_fp
    blended = int(round(h_fp * 0.45 + ai_fp * 0.55))
    blended = max(0, min(100, blended))
    data["failure_probability"] = blended
    for key, hint_key in (
        ("dropout_risk", "dropout_risk_hint"),
        ("burnout_risk", "burnout_risk_hint"),
        ("intervention_urgency", "intervention_urgency_hint"),
    ):
        if str(data.get(key, "")).lower() not in {"low", "medium", "high"}:
            data[key] = str(heuristic[hint_key])

    if not isinstance(data.get("recommended_interventions"), list):
        data["recommended_interventions"] = [
            "Schedule a supportive academic advising session.",
            "Offer structured revision resources for weakest topics.",
        ]
    if not data.get("rationale"):
        data["rationale"] = (
            "Signals combine attendance, formative performance, engagement, and past misses "
            f"into an advisory composite around {blended}/100 pressure with "
            f"{data.get('dropout_risk', 'medium')} dropout concern."
        )

    try:
        return PredictAcademicRiskResponse.model_validate(data)
    except ValidationError as e:
        logger.warning("Prediction validation failed: %s", e)
        return PredictAcademicRiskResponse(
            success=True,
            failure_probability=h_fp,
            dropout_risk=str(heuristic["dropout_risk_hint"]),
            burnout_risk=str(heuristic["burnout_risk_hint"]),
            predicted_grade="C",
            intervention_urgency=str(heuristic["intervention_urgency_hint"]),
            recommended_interventions=list(data.get("recommended_interventions") or []),
            rationale=str(data.get("rationale") or "Heuristic-only fallback due to parse issues."),
        )


class PredictionService:
    def __init__(self) -> None:
        self._openai = OpenAIService()

    @property
    def is_configured(self) -> bool:
        return self._openai.is_configured

    async def predict(self, body: PredictAcademicRiskRequest) -> PredictAcademicRiskResponse:
        heuristic = compute_heuristic(body.student_data)
        messages = build_prediction_messages(body, heuristic)
        raw = await self._openai.complete_json(messages, temperature=0.22)
        if not isinstance(raw, dict):
            raise ValueError("Model output must be a JSON object.")
        return _coerce(raw, heuristic)
