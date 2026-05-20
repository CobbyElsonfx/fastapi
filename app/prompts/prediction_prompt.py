"""Prompts for academic risk prediction JSON."""

from __future__ import annotations

import json
from typing import Any

from app.schemas.prediction_schema import PredictAcademicRiskRequest

SYSTEM = """You are an academic success advisor. Interpret risk metrics and return JSON only.

Rules:
- Combine heuristic guidance with qualitative reasoning; predictions are advisory, not fate.
- dropout_risk, burnout_risk, intervention_urgency: use low|medium|high.
- predicted_grade: single letter A-F scale (use + if needed, e.g. B+).
- recommended_interventions: 3-6 concrete, caring actions.
- rationale: 2-4 sentences explaining the assessment without alarming language.
- Return ONLY valid JSON. No markdown."""


def build_prediction_messages(
    body: PredictAcademicRiskRequest,
    heuristic: dict[str, Any],
) -> list[dict[str, Any]]:
    schema = {
        "success": True,
        "failure_probability": "0-100 int",
        "dropout_risk": "low|medium|high",
        "burnout_risk": "low|medium|high",
        "predicted_grade": "string",
        "intervention_urgency": "low|medium|high",
        "recommended_interventions": ["string"],
        "rationale": "string",
    }
    payload = {
        "student_data": body.student_data.model_dump(),
        "heuristic_baselines": heuristic,
    }
    user = (
        "Use these quantitative signals (heuristics are advisory baselines, you may adjust slightly with justification in rationale):\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Return JSON shaped like:\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
