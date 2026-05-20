"""Prompts for institutional analytics JSON."""

from __future__ import annotations

import json
from typing import Any

from app.schemas.analytics_schema import AnalyzeAcademicIntelligenceRequest

SYSTEM = """You are an institutional learning analytics lead. Summarize cohort health as JSON only.

Rules:
- Identify weak topics, at-risk patterns, and constructive interventions.
- at_risk_students: list of objects with keys student_id, reason, suggested_action.
- performance_clusters: list of objects with label, count_or_percent, description.
- summary, department_insights, cohort_trends: arrays of short bullet strings.
- course_health_score: 0-100 integer.
- Return ONLY valid JSON. No markdown."""


def build_analytics_messages(body: AnalyzeAcademicIntelligenceRequest) -> list[dict[str, Any]]:
    schema = {
        "success": True,
        "course_health_score": "int 0-100",
        "at_risk_students": [{"student_id": 0, "reason": "", "suggested_action": ""}],
        "weak_topics": ["string"],
        "performance_clusters": [{"label": "", "share": "", "description": ""}],
        "interventions": ["string"],
        "summary": ["string"],
        "department_insights": ["string"],
        "cohort_trends": ["string"],
    }
    payload = body.model_dump(mode="json")
    user = (
        "Cohort dataset:\n"
        f"{json.dumps(payload, ensure_ascii=False)[:120_000]}\n\n"
        "Return JSON shaped like:\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
