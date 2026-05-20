"""Schemas for AI Learning Twin generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateLearningTwinRequest(BaseModel):
    student: dict[str, Any] = Field(default_factory=dict)
    academic_data: dict[str, Any] = Field(default_factory=dict)
    topic_performance: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    recent_attempts: list[dict[str, Any]] = Field(default_factory=list, max_length=200)


class GenerateLearningTwinResponse(BaseModel):
    success: bool = True
    academic_health_score: int = Field(default=50, ge=0, le=100)
    risk_level: str = "medium"
    predicted_next_score: int = Field(default=50, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    learning_pattern: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    revision_focus: list[str] = Field(default_factory=list)
    lecturer_intervention: str = ""
