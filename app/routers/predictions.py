"""HTTP routes for academic risk prediction."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.prediction_schema import PredictAcademicRiskRequest, PredictAcademicRiskResponse
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predictions"])
_service = PredictionService()


@router.post(
    "/predict-academic-risk",
    response_model=PredictAcademicRiskResponse,
    summary="Predict academic risk and interventions",
)
async def predict_academic_risk(body: PredictAcademicRiskRequest) -> PredictAcademicRiskResponse:
    if not _service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured: set OPENAI_API_KEY in .env",
        )
    try:
        return await _service.predict(body)
    except ValueError as e:
        logger.warning("Prediction error: %s", e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI provider error. Please retry later.",
        ) from e
