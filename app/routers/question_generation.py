"""Question generation HTTP routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.config.settings import settings
from app.prompts.question_prompt import build_question_generation_messages
from app.schemas.question_schema import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
)
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["question-generation"])

_openai = OpenAIService()


@router.post(
    "/generate-questions",
    response_model=GenerateQuestionsResponse,
    summary="Generate assessment questions via OpenAI",
)
async def generate_questions(body: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    if not _openai.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )

    messages = build_question_generation_messages(body)
    try:
        questions = await _openai.generate_questions(body, messages)
    except ValueError as e:
        logger.warning("Validation / parse error: %s", e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.exception("OpenAI generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e

    return GenerateQuestionsResponse(
        success=True,
        model=settings.openai_model,
        questions=questions,
    )
