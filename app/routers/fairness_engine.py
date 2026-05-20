"""Exam fairness analysis HTTP routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.fairness_schema import AnalyzeExamFairnessRequest, AnalyzeExamFairnessResponse
from app.services.fairness_service import analyze_exam_fairness
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exam-fairness"])

_openai = OpenAIService()


@router.post(
    "/analyze-exam-fairness",
    summary="AI-powered exam fairness and quality review",
)
async def analyze_exam_fairness_endpoint(
    body: AnalyzeExamFairnessRequest,
) -> AnalyzeExamFairnessResponse:
    if not _openai.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )

    if not body.questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Add questions before running fairness analysis.",
        )

    try:
        result = await analyze_exam_fairness(body, _openai.complete_json)
    except ValueError as e:
        logger.warning("Fairness validation error: %s", e)
        return AnalyzeExamFairnessResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Fairness analysis failed: %s", e)
        return AnalyzeExamFairnessResponse(
            success=False,
            error="Upstream AI provider error. Please retry later.",
        )

    return result
