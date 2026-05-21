"""
FastAPI entrypoint for the AI Academic Intelligence Operating System — AI layer.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routers import (
    analytics_intelligence,
    fairness_engine,
    learning_twin,
    mark_answer,
    practice_feedback,
    predictions,
    question_generation,
    revision_plan,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "AI microservice for the university assessment platform. "
        "Designed to be called from Laravel via HTTP. "
        "Extensions may add: /mark-answer, /analyze-exam-fairness, "
        "/predict-performance-risk, /oral-examiner."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(question_generation.router)
app.include_router(revision_plan.router)
app.include_router(learning_twin.router)
app.include_router(predictions.router)
app.include_router(analytics_intelligence.router)
app.include_router(practice_feedback.router)
app.include_router(fairness_engine.router)
app.include_router(mark_answer.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe for orchestrators and Laravel health checks."""
    return {"status": "ok"}


@app.get("/", tags=["meta"])
async def root() -> dict[str, Any]:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "generate_questions": "/generate-questions",
        "generate_revision_plan": "/generate-revision-plan",
        "generate_learning_twin": "/generate-learning-twin",
        "predict_academic_risk": "/predict-academic-risk",
        "analyze_academic_intelligence": "/analyze-academic-intelligence",
        "generate_practice_feedback": "/generate-practice-feedback",
        "analyze_exam_fairness": "/analyze-exam-fairness",
        "mark_answer": "/mark-answer",
    }
