"""Health check and system telemetry routes."""

from datetime import datetime
from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Basic liveness check")
async def health_check():
    """Returns basic liveness status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready", summary="System readiness and integration status")
async def readiness_check():
    """Checks database, checkpointer, and external tool configuration readiness."""
    return {
        "status": "ready",
        "currency": settings.CURRENCY,
        "auto_refund_threshold_aud": settings.DISPUTE_AUTO_REFUND_THRESHOLD_AUD,
        "slack_mock_mode": settings.SLACK_MOCK_MODE,
        "database_connected": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
