"""Orchestrate OpenAI JSON output → validated fairness response."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.prompts.fairness_prompt import build_fairness_messages
from app.schemas.fairness_schema import (
    AnalyzeExamFairnessRequest,
    AnalyzeExamFairnessResponse,
    BloomsDistribution,
    DifficultyDistribution,
)

logger = logging.getLogger(__name__)


def _coerce_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "y"}
    return bool(v)


def _normalize_question_row(
    raw: dict[str, Any],
    fallback_id: int,
    fallback_num: int,
    fallback_text: str,
) -> dict[str, Any]:
    out = dict(raw)
    out.setdefault("question_id", fallback_id)
    out.setdefault("question_number", fallback_num)
    out.setdefault("question", fallback_text)
    out.setdefault("difficulty", "Medium")
    out.setdefault("blooms_level", "Understand")
    out.setdefault("estimated_time_minutes", 1.0)
    out.setdefault("syllabus_alignment", "Unknown")
    for k in (
        "ambiguity_detected",
        "excessive_difficulty",
        "repeated_pattern",
        "bias_detected",
        "trick_question_detected",
    ):
        out[k] = _coerce_bool(out.get(k, False))
    issues = out.get("issues")
    if not isinstance(issues, list):
        issues = []
    cleaned = []
    for it in issues:
        if isinstance(it, dict):
            cleaned.append(
                {
                    "type": str(it.get("type", "other")),
                    "severity": it.get("severity", "medium"),
                    "message": str(it.get("message", "")),
                    "suggestion": str(it.get("suggestion", "")),
                }
            )
    out["issues"] = cleaned
    out.setdefault("improved_question", "")
    return out


def normalize_ai_payload(
    data: dict[str, Any],
    request: AnalyzeExamFairnessRequest,
) -> dict[str, Any]:
    """Merge model output with request question metadata when the model omits fields."""
    by_num = {q.question_number: q for q in request.questions}
    by_id = {q.question_id: q for q in request.questions}

    q_rows = data.get("question_analysis")
    if not isinstance(q_rows, list):
        q_rows = []

    merged_analysis: list[dict[str, Any]] = []
    for i, row in enumerate(q_rows):
        if not isinstance(row, dict):
            continue
        qid = int(row.get("question_id") or 0)
        qnum = int(row.get("question_number") or 0)
        src = by_num.get(qnum) or by_id.get(qid)
        if src is None and i < len(request.questions):
            src = request.questions[i]
        if src is None:
            continue
        merged_analysis.append(
            _normalize_question_row(
                row,
                src.question_id,
                src.question_number,
                src.question,
            )
        )

    # Ensure one row per input question if model returned fewer
    seen = {r["question_id"] for r in merged_analysis}
    for q in request.questions:
        if q.question_id not in seen:
            merged_analysis.append(
                _normalize_question_row(
                    {
                        "question_id": q.question_id,
                        "question_number": q.question_number,
                        "question": q.question,
                        "syllabus_alignment": "Unknown" if not request.topics else "Partially aligned",
                        "issues": [],
                    },
                    q.question_id,
                    q.question_number,
                    q.question,
                )
            )

    merged_analysis.sort(key=lambda r: r["question_number"])
    data["question_analysis"] = merged_analysis

    data.setdefault("fairness_score", 0)
    data.setdefault("overall_status", "Unknown")
    data.setdefault("estimated_total_duration_minutes", 0)
    data.setdefault("duration_status", "Unknown")

    cmap = data.get("cognitive_difficulty_map")
    if not isinstance(cmap, list) or len(cmap) == 0:
        data["cognitive_difficulty_map"] = [
            {
                "question_number": r["question_number"],
                "difficulty": r["difficulty"],
                "blooms_level": r["blooms_level"],
                "estimated_time_minutes": float(r.get("estimated_time_minutes", 1)),
            }
            for r in merged_analysis
        ]

    dd = data.get("difficulty_distribution")
    if not isinstance(dd, dict):
        data["difficulty_distribution"] = DifficultyDistribution().model_dump()
    else:
        data["difficulty_distribution"] = DifficultyDistribution.model_validate(dd).model_dump()

    bd = data.get("blooms_distribution")
    if not isinstance(bd, dict):
        data["blooms_distribution"] = BloomsDistribution().model_dump()
    else:
        data["blooms_distribution"] = BloomsDistribution.model_validate(bd).model_dump()

    recs = data.get("recommendations")
    if not isinstance(recs, list):
        data["recommendations"] = []
    else:
        data["recommendations"] = [str(x) for x in recs if str(x).strip()]

    return data


async def analyze_exam_fairness(
    body: AnalyzeExamFairnessRequest,
    complete_json,
) -> AnalyzeExamFairnessResponse:
    """
    complete_json: bound method OpenAIService.complete_json
    """
    if not body.questions:
        return AnalyzeExamFairnessResponse(
            success=False,
            error="No questions supplied for fairness analysis.",
        )

    messages = build_fairness_messages(body)

    raw = await complete_json(messages, temperature=0.25)
    if not isinstance(raw, dict):
        raise ValueError("Model returned non-object JSON.")

    normalized = normalize_ai_payload(raw, body)
    normalized["success"] = True
    normalized.pop("error", None)

    try:
        return AnalyzeExamFairnessResponse.model_validate(normalized)
    except ValidationError as e:
        logger.error("Fairness response validation failed: %s", e)
        raise ValueError("Fairness analysis JSON failed validation.") from e
