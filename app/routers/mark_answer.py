"""Exam script marking — theory / fill-in via concept-based AI evaluation."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.mark_answer_schema import MarkAnswerRequest, MarkAnswerResponse
from app.services.mark_answer_service import MarkAnswerService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["script-marking"])

_service = MarkAnswerService()


@router.post(
    "/mark-answer",
    response_model=MarkAnswerResponse,
    summary="Mark a theory or fill-in exam answer (concept-based JSON evaluation)",
)
async def mark_answer(body: MarkAnswerRequest) -> MarkAnswerResponse:
    if not _service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in ai-service .env",
        )

    try:
        return await _service.mark(body)
    except ValueError as e:
        logger.warning("Mark answer validation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except Exception as e:
        logger.exception("Mark answer failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e
