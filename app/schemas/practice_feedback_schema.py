"""Pydantic models for practice quiz feedback."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratePracticeFeedbackRequest(BaseModel):
    student_score: int = Field(..., ge=0, le=100, description="Percentage score 0–100")
    course: str = Field(..., min_length=1, max_length=200)
    weak_topics: list[str] = Field(default_factory=list)
    failed_questions: list[str] = Field(default_factory=list)
    difficulty_level: str = Field(default="medium", max_length=32)
    available_quiz_titles: list[str] = Field(default_factory=list)


class GeneratePracticeFeedbackResponse(BaseModel):
    summary: str
    recommended_topics: list[str] = Field(default_factory=list)
    revision_tips: list[str] = Field(default_factory=list)
    recommended_quizzes: list[str] = Field(default_factory=list)
    motivation_message: str
