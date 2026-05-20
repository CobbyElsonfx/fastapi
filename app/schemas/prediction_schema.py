"""Schemas for academic risk prediction."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StudentRiskData(BaseModel):
    attendance: float | int = Field(default=0, ge=0, le=100)
    quiz_average: float | int = Field(default=0, ge=0, le=100)
    assignment_average: float | int = Field(default=0, ge=0, le=100)
    engagement: float | int = Field(default=0, ge=0, le=100)
    previous_failures: int = Field(default=0, ge=0, le=50)
    missed_assessments: int = Field(default=0, ge=0, le=50)


class PredictAcademicRiskRequest(BaseModel):
    student_data: StudentRiskData


class PredictAcademicRiskResponse(BaseModel):
    success: bool = True
    failure_probability: int = Field(default=50, ge=0, le=100)
    dropout_risk: str = "medium"
    burnout_risk: str = "medium"
    predicted_grade: str = "C"
    intervention_urgency: str = "medium"
    recommended_interventions: list[str] = Field(default_factory=list)
    rationale: str = Field(
        default="",
        description="Short explanation of why risks were assessed this way (advisory).",
    )
