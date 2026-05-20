"""System + user messages for practice feedback."""

from __future__ import annotations

from typing import Any

from app.schemas.practice_feedback_schema import GeneratePracticeFeedbackRequest


def build_practice_feedback_messages(body: GeneratePracticeFeedbackRequest) -> list[dict[str, Any]]:
    system = (
        "You are a supportive university learning coach. The student completed a self-paced PRACTICE quiz "
        "(not a high-stakes exam). Respond ONLY with valid JSON matching the schema keys: "
        "summary, recommended_topics, revision_tips, recommended_quizzes, motivation_message. "
        "Use encouraging, respectful language. Never insult or shame. Give practical, concrete study steps. "
        "recommended_quizzes should be short titles drawn from available_quiz_titles when possible, "
        "or plausible short quiz titles aligned with the course if the list is empty. "
        "Keep lists concise (max ~6 items each). summary: 2–4 sentences."
    )
    user = {
        "student_score_percent": body.student_score,
        "course": body.course,
        "weak_topics": body.weak_topics,
        "failed_questions": body.failed_questions,
        "difficulty_level": body.difficulty_level,
        "available_quiz_titles": body.available_quiz_titles,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": __import__("json").dumps(user)},
    ]
