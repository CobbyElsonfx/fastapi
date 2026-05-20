"""Prompts for learning twin JSON."""

from __future__ import annotations

import json
from typing import Any

from app.schemas.learning_twin_schema import GenerateLearningTwinRequest

SYSTEM = """You are a supportive university learning scientist. Build a concise digital learning twin profile as JSON only.

Rules:
- Encouraging, respectful, never insulting.
- Strengths and weaknesses must be grounded in the supplied metrics and attempts.
- Predictions are advisory — avoid absolute claims; use ranges implicitly via integers.
- recommended_actions and revision_focus must be practical and specific.
- Return ONLY valid JSON matching the user schema. No markdown fences."""


def build_learning_twin_messages(body: GenerateLearningTwinRequest) -> list[dict[str, Any]]:
    schema = {
        "success": True,
        "academic_health_score": "0-100 int",
        "risk_level": "low|medium|high",
        "predicted_next_score": "0-100 int (next assessment expectation)",
        "strengths": ["string"],
        "weaknesses": ["string"],
        "learning_pattern": "one paragraph",
        "recommended_actions": ["string"],
        "revision_focus": ["string"],
        "lecturer_intervention": "one short paragraph for the lecturer",
    }
    payload = {
        "student": body.student,
        "academic_data": body.academic_data,
        "topic_performance": body.topic_performance,
        "recent_attempts": body.recent_attempts,
    }
    user = (
        "Context JSON:\n"
        f"{json.dumps(payload, ensure_ascii=False)[:100_000]}\n\n"
        "Respond with JSON shaped like:\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
