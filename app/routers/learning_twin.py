"""HTTP routes for AI Learning Twin."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.learning_twin_schema import GenerateLearningTwinRequest, GenerateLearningTwinResponse
from app.services.learning_twin_service import LearningTwinService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["learning-twin"])
_service = LearningTwinService()


@router.post(
    "/generate-learning-twin",
    response_model=GenerateLearningTwinResponse,
    summary="Generate a digital learning twin profile",
)
async def generate_learning_twin(body: GenerateLearningTwinRequest) -> GenerateLearningTwinResponse:
    if not _service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )
    try:
        return await _service.generate(body)
    except ValueError as e:
        logger.warning("Learning twin error: %s", e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.exception("Learning twin failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e
