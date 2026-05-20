"""System + user messages for revision plan JSON generation."""

from __future__ import annotations

import json
from typing import Any

from app.schemas.revision_plan_schema import GenerateRevisionPlanRequest

SYSTEM_PROMPT = """You are an expert university learning coach. Produce a personalized revision plan as JSON only.

Rules:
- Be encouraging, respectful, and growth-focused. Never insult or shame the student.
- Explain weak areas clearly in plain language.
- Use the provided weak topics and failed questions as signals; do not invent grades.
- Practice questions must be NEW scenarios that build the same skills; do not copy exam items verbatim.
- Do NOT leak exact answers for future high-stakes exams; use explanations and learning prompts instead.
- Flashcards should reinforce concepts, not just repeat secret keys from the original exam.
- Return ONLY one JSON object matching the schema described in the user message. No markdown fences, no prose outside JSON.
"""


def build_revision_plan_messages(body: GenerateRevisionPlanRequest) -> list[dict[str, Any]]:
    schema_hint = {
        "success": True,
        "risk_level": "low | medium | high",
        "summary": "2–4 sentences",
        "weak_topics": ["string"],
        "revision_notes": [{"topic": "string", "note": "string"}],
        "flashcards": [{"front": "string", "back": "string"}],
        "practice_questions": [
            {"topic": "string", "type": "short_answer|mcq|theory", "question": "string", "expected_answer": "string"}
        ],
        "study_plan": [{"day": 1, "title": "string", "tasks": ["string"]}],
        "recommended_actions": ["string"],
    }

    payload = body.model_dump(mode="json")
    user = (
        "Student performance context (JSON):\n"
        f"{json.dumps(payload, ensure_ascii=False)[:120_000]}\n\n"
        "Respond with JSON exactly shaped like this example structure (fill with real content):\n"
        f"{json.dumps(schema_hint, ensure_ascii=False)}\n\n"
        "Set success to true. Align weak_topics with the student's needs. "
        "Include at least 3 revision_notes if topics exist, else fewer. "
        "Include 4–8 flashcards when helpful. Include 3–6 practice_questions. "
        "study_plan should cover about 5–7 days with concrete tasks."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
