"""Schemas for cohort / institutional analytics."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CohortStudentRow(BaseModel):
    model_config = {"extra": "allow"}

    student_id: int | str = 0
    average_score: float | int = 0
    attendance: float | int = Field(default=0, ge=0, le=100)
    quiz_average: float | int = Field(default=0, ge=0, le=100)
    assignment_average: float | int = Field(default=0, ge=0, le=100)
    engagement_score: float | int = Field(default=0, ge=0, le=100)


class AnalyzeAcademicIntelligenceRequest(BaseModel):
    course: str = Field(default="", max_length=300)
    department: str | None = Field(default=None, max_length=200)
    students: list[CohortStudentRow] = Field(default_factory=list, max_length=2000)


class AnalyzeAcademicIntelligenceResponse(BaseModel):
    success: bool = True
    course_health_score: int = Field(default=50, ge=0, le=100)
    at_risk_students: list[dict[str, Any]] = Field(default_factory=list)
    weak_topics: list[str] = Field(default_factory=list)
    performance_clusters: list[dict[str, Any]] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    summary: list[str] = Field(default_factory=list)
    department_insights: list[str] = Field(default_factory=list)
    cohort_trends: list[str] = Field(default_factory=list)
