"""Pydantic models for personalized revision plan generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FailedQuestionIn(BaseModel):
    question: str = ""
    student_answer: str = ""
    correct_answer: str = ""
    topic: str = "General"
    marks: int = 0
    score_awarded: int = 0


class PerformanceHistoryItem(BaseModel):
    assessment: str = ""
    score: float | int = 0


class GenerateRevisionPlanRequest(BaseModel):
    student_id: int
    student_name: str = "Student"
    course: str = Field(default="", max_length=300)
    exam_title: str = Field(default="", max_length=300)
    overall_score: float | int = 0
    overall_percent: float | int | None = None
    weak_topics: list[str] = Field(default_factory=list, max_length=50)
    failed_questions: list[FailedQuestionIn] = Field(default_factory=list, max_length=200)
    performance_history: list[PerformanceHistoryItem] = Field(default_factory=list, max_length=30)


class RevisionNoteOut(BaseModel):
    topic: str = ""
    note: str = ""


class FlashcardOut(BaseModel):
    front: str = ""
    back: str = ""


class PracticeQuestionOut(BaseModel):
    topic: str = ""
    type: str = "short_answer"
    question: str = ""
    expected_answer: str = ""


class StudyPlanDayOut(BaseModel):
    day: int = 1
    title: str = ""
    tasks: list[str] = Field(default_factory=list)


class GenerateRevisionPlanResponse(BaseModel):
    success: bool = True
    risk_level: str = "medium"
    summary: str = ""
    weak_topics: list[str] = Field(default_factory=list)
    revision_notes: list[RevisionNoteOut] = Field(default_factory=list)
    flashcards: list[FlashcardOut] = Field(default_factory=list)
    practice_questions: list[PracticeQuestionOut] = Field(default_factory=list)
    study_plan: list[StudyPlanDayOut] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
