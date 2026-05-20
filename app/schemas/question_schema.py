"""Pydantic models for question generation API."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

QuestionType = Literal["mcq", "fill_in", "short_answer", "theory"]
Difficulty = Literal["easy", "medium", "hard"]

# Rough cap so one request stays within typical model context (notes + instructions).
_MAX_NOTES_CHARS = 120_000


class GenerateQuestionsRequest(BaseModel):
    """Inbound payload from Laravel or other HTTP clients."""

    course: str = Field(..., min_length=1, max_length=200)
    topic: str = Field(..., min_length=1, max_length=200)
    difficulty: Difficulty = "medium"
    question_type: QuestionType = "mcq"
    number_of_questions: int = Field(default=5, ge=1, le=100)
    lecture_notes: str | None = Field(
        default=None,
        max_length=500_000,
        description="Lecture notes / source text to ground questions in (truncated server-side if very long).",
    )
    question_types: list[QuestionType] | None = Field(
        default=None,
        max_length=20,
        description="If set, question i uses question_types[(question_type_offset + i) % len]. "
        "Otherwise all items use question_type.",
    )
    question_type_offset: int = Field(
        default=0,
        ge=0,
        le=10_000,
        description="Global index of the first question in this batch (for Laravel chunking).",
    )
    learning_outcome: str | None = Field(default=None, max_length=2000)

    @field_validator("course", "topic", mode="before")
    @classmethod
    def strip_strings(cls, v: object) -> str:
        if v is None:
            raise ValueError("must be a non-empty string")
        s = str(v).strip()
        if not s:
            raise ValueError("must not be blank")
        return s

    @field_validator("lecture_notes", mode="before")
    @classmethod
    def strip_truncate_notes(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if len(s) > _MAX_NOTES_CHARS:
            return s[:_MAX_NOTES_CHARS]
        return s

    @field_validator("learning_outcome", mode="before")
    @classmethod
    def strip_learning_outcome(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("question_types", mode="before")
    @classmethod
    def empty_types_to_none(cls, v: object) -> list[QuestionType] | None:
        if v is None:
            return None
        if isinstance(v, list) and len(v) == 0:
            return None
        return v  # type: ignore[return-value]


class GeneratedQuestion(BaseModel):
    """One generated item — shape varies slightly by type; options empty when N/A."""

    question: str = Field(..., min_length=1)
    question_type: QuestionType | None = Field(
        default=None,
        description="Item type; required when request uses mixed question_types.",
    )
    options: list[str] = Field(default_factory=list)
    correct_answer: str = Field(..., min_length=1)
    explanation: str = Field(default="")


class GenerateQuestionsResponse(BaseModel):
    """Stable JSON envelope for HTTP clients."""

    success: bool = True
    model: str = Field(default="", description="Upstream LLM model id used for this run.")
    questions: list[GeneratedQuestion] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    success: bool = False
    detail: str
