"""HTTP routes for institutional academic analytics."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.analytics_schema import AnalyzeAcademicIntelligenceRequest, AnalyzeAcademicIntelligenceResponse
from app.services.analytics_service import AnalyticsIntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics-intelligence"])
_service = AnalyticsIntelligenceService()


@router.post(
    "/analyze-academic-intelligence",
    response_model=AnalyzeAcademicIntelligenceResponse,
    summary="Analyze cohort academic intelligence",
)
async def analyze_academic_intelligence(
    body: AnalyzeAcademicIntelligenceRequest,
) -> AnalyzeAcademicIntelligenceResponse:
    if not _service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )
    try:
        return await _service.analyze(body)
    except ValueError as e:
        logger.warning("Analytics error: %s", e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.exception("Analytics failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e
