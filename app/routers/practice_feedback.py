"""Practice hub — supportive feedback after a practice attempt."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.practice_feedback_schema import GeneratePracticeFeedbackRequest, GeneratePracticeFeedbackResponse
from app.services.practice_feedback_service import PracticeFeedbackService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["practice-feedback"])

_service = PracticeFeedbackService()


@router.post(
    "/generate-practice-feedback",
    response_model=GeneratePracticeFeedbackResponse,
    summary="Post-practice supportive feedback and revision guidance",
)
async def generate_practice_feedback(body: GeneratePracticeFeedbackRequest) -> GeneratePracticeFeedbackResponse:
    if not _service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )

    try:
        return await _service.generate(body)
    except ValueError as e:
        logger.warning("Practice feedback validation error: %s", e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.exception("Practice feedback generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e
