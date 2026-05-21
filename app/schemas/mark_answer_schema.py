"""Pydantic models for exam script marking (theory / fill-in)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class MarkAnswerRequest(BaseModel):
    question_text: str = Field(..., min_length=1)
    student_answer: str = Field(default="")
    student_response: str | None = Field(
        default=None,
        description="Legacy alias for student_answer (Laravel external client).",
    )
    model_answer: str | None = None
    question_type: str = Field(default="theory", max_length=32)
    max_marks: int = Field(..., ge=0, le=1000)
    evaluation_format: str | None = Field(default="json_v1")

    @field_validator("question_type", mode="before")
    @classmethod
    def normalize_type(cls, v: object) -> str:
        s = str(v or "theory").strip().lower()
        if s == "short_answer":
            return "theory"
        return s or "theory"

    def resolved_student_answer(self) -> str:
        if self.student_answer.strip():
            return self.student_answer
        return (self.student_response or "").strip()


class MarkAnswerResponse(BaseModel):
    marks_awarded: float = Field(..., ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    evaluation_status: str | None = None
    detected_concepts: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    concept_coverage: float | None = Field(default=None, ge=0, le=1)
    key_concepts_rubric: list[str] = Field(default_factory=list)
    reason: str | None = None
    feedback: str | None = None
