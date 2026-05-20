"""Personalized revision plan HTTP routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.revision_plan_schema import GenerateRevisionPlanRequest, GenerateRevisionPlanResponse
from app.services.revision_plan_service import RevisionPlanService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["revision-plan"])

_service = RevisionPlanService()


@router.post(
    "/generate-revision-plan",
    response_model=GenerateRevisionPlanResponse,
    summary="Generate a personalized revision plan from attempt performance",
)
async def generate_revision_plan(body: GenerateRevisionPlanRequest) -> GenerateRevisionPlanResponse:
    if not _service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )

    try:
        return await _service.generate(body)
    except ValueError as e:
        logger.warning("Revision plan validation / parse error: %s", e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.exception("Revision plan generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e
