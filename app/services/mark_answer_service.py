"""Exam script marking via OpenAI (concept-based evaluation)."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.mark_answer_prompt import build_mark_answer_messages
from app.schemas.mark_answer_schema import MarkAnswerRequest, MarkAnswerResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

_FAIRNESS_SUFFIX = (
    " Partial-credit alignment: at least one relevant concept was identified; "
    "marks raised to reflect concept-based fairness."
)


def _round_half(x: float) -> float:
    return round(x * 2) / 2.0


def _apply_theory_fairness_guard(
    data: dict[str, Any],
    *,
    max_marks: int,
    student_answer: str,
    question_type: str,
) -> dict[str, Any]:
    if question_type != "theory" or max_marks <= 0:
        return data

    text = student_answer.strip()
    if len(text) < 8:
        return data

    marks = float(data.get("marks_awarded") or 0)
    if marks > 0.0001:
        return data

    detected = data.get("detected_concepts") or []
    missing = data.get("missing_concepts") or []
    if not isinstance(detected, list):
        detected = []
    if not isinstance(missing, list):
        missing = []
    detected = [str(c) for c in detected if str(c).strip()]
    missing = [str(c) for c in missing if str(c).strip()]

    if not detected:
        return data

    max_f = float(max_marks)
    min_partial = min(max_f, max(0.5, round(max_f * 0.25 * 2) / 2.0))

    if not missing:
        suggested = min_partial
    else:
        ratio = len(detected) / max(1, len(detected) + len(missing))
        coverage = data.get("concept_coverage")
        if coverage is not None:
            try:
                cov = max(ratio, float(coverage))
            except (TypeError, ValueError):
                cov = ratio
            from_coverage = max_f * cov
        else:
            from_coverage = max_f * ratio
        suggested = min(max_f, max(min_partial, _round_half(from_coverage)))

    reason = str(data.get("reason") or "").strip()
    data["marks_awarded"] = suggested
    data["evaluation_status"] = "correct" if suggested + 0.001 >= max_f else "partial"
    data["reason"] = (
        f"{reason}{_FAIRNESS_SUFFIX}" if reason else _FAIRNESS_SUFFIX.strip()
    )
    return data


def _coerce_response(raw: dict[str, Any], max_marks: int) -> MarkAnswerResponse:
    marks = float(raw.get("marks_awarded", 0))
    marks = max(0.0, min(float(max_marks), marks))

    payload = dict(raw)
    payload["marks_awarded"] = marks

    for key in ("detected_concepts", "missing_concepts", "key_concepts_rubric"):
        val = payload.get(key)
        if not isinstance(val, list):
            payload[key] = []
        else:
            payload[key] = [str(x) for x in val if str(x).strip()]

    if payload.get("confidence") is not None:
        try:
            payload["confidence"] = max(0.0, min(1.0, float(payload["confidence"])))
        except (TypeError, ValueError):
            payload["confidence"] = None

    if payload.get("concept_coverage") is not None:
        try:
            payload["concept_coverage"] = max(
                0.0, min(1.0, float(payload["concept_coverage"]))
            )
        except (TypeError, ValueError):
            payload["concept_coverage"] = None

    try:
        return MarkAnswerResponse.model_validate(payload)
    except ValidationError as e:
        logger.warning("Mark answer validation fallback: %s", e)
        return MarkAnswerResponse(
            marks_awarded=marks,
            evaluation_status=str(raw.get("evaluation_status") or "unknown"),
            reason=str(raw.get("reason") or "Model returned partial JSON."),
            feedback=str(raw.get("feedback") or None) or None,
        )


class MarkAnswerService:
    def __init__(self) -> None:
        self._openai = OpenAIService()

    @property
    def is_configured(self) -> bool:
        return self._openai.is_configured

    async def mark(self, body: MarkAnswerRequest) -> MarkAnswerResponse:
        student = body.resolved_student_answer()
        q_type = body.question_type

        if not student.strip():
            return MarkAnswerResponse(
                marks_awarded=0.0,
                confidence=0.0,
                evaluation_status="unanswered",
                concept_coverage=0.0,
                reason="No student answer provided.",
                feedback="Provide an answer before submission.",
            )

        if body.max_marks <= 0:
            return MarkAnswerResponse(
                marks_awarded=0.0,
                evaluation_status="n/a",
                reason="Question has zero marks.",
            )

        temperature = 0.35 if q_type == "theory" else 0.2
        messages = build_mark_answer_messages(
            question_text=body.question_text,
            student_answer=student,
            max_marks=body.max_marks,
            question_type=q_type,
            model_answer=body.model_answer,
        )
        raw = await self._openai.complete_json(messages, temperature=temperature)
        if not isinstance(raw, dict):
            raise ValueError("Model output must be a JSON object.")

        if q_type == "theory":
            raw = _apply_theory_fairness_guard(
                raw,
                max_marks=body.max_marks,
                student_answer=student,
                question_type=q_type,
            )

        return _coerce_response(raw, body.max_marks)
