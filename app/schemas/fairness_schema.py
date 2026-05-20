"""Request/response schemas for exam fairness analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FairnessQuestionIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question_id: int
    question_number: int
    type: str
    question: str
    options: list[str] | None = None
    marks: int = 0


class AnalyzeExamFairnessRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    exam_id: int
    exam_title: str
    course: str
    expected_duration_minutes: int = Field(ge=0)
    topics: list[str] = Field(default_factory=list)
    questions: list[FairnessQuestionIn]


class FairnessIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    severity: str = "medium"
    message: str
    suggestion: str = ""


class QuestionFairnessAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question_id: int
    question_number: int
    question: str = ""
    difficulty: str = "Medium"
    blooms_level: str = "Understand"
    estimated_time_minutes: float = 1.0
    syllabus_alignment: str = "Unknown"
    ambiguity_detected: bool = False
    excessive_difficulty: bool = False
    repeated_pattern: bool = False
    bias_detected: bool = False
    trick_question_detected: bool = False
    issues: list[FairnessIssue] = Field(default_factory=list)
    improved_question: str = ""


class CognitiveMapItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question_number: int
    difficulty: str = "Medium"
    blooms_level: str = "Understand"
    estimated_time_minutes: float = 1.0


class DifficultyDistribution(BaseModel):
    model_config = ConfigDict(extra="ignore")

    easy: float = 0
    medium: float = 0
    hard: float = 0
    very_hard: float = 0


class BloomsDistribution(BaseModel):
    model_config = ConfigDict(extra="ignore")

    remember: float = 0
    understand: float = 0
    apply: float = 0
    analyze: float = 0
    evaluate: float = 0
    create: float = 0


class AnalyzeExamFairnessResponse(BaseModel):
    """Shape returned to Laravel (JSON)."""

    model_config = ConfigDict(extra="ignore")

    success: bool = True
    error: str | None = None
    fairness_score: int | None = None
    overall_status: str | None = None
    estimated_total_duration_minutes: int | None = None
    duration_status: str | None = None
    difficulty_distribution: DifficultyDistribution | None = None
    blooms_distribution: BloomsDistribution | None = None
    cognitive_difficulty_map: list[CognitiveMapItem] = Field(default_factory=list)
    question_analysis: list[QuestionFairnessAnalysis] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    def model_dump_json_safe(self) -> dict[str, Any]:
        d = self.model_dump(mode="python")
        if self.difficulty_distribution is not None:
            d["difficulty_distribution"] = self.difficulty_distribution.model_dump()
        if self.blooms_distribution is not None:
            d["blooms_distribution"] = self.blooms_distribution.model_dump()
        return d
