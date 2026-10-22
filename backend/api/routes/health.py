"""
NØX - Health & Readiness Route
Provides server readiness, model status, and runtime environment telemetry.
"""

from fastapi import APIRouter, Request
from backend.api.schemas.detection_schema import HealthResponseSchema

router = APIRouter(prefix="/api", tags=["System Health"])


@router.get(
    "/health",
    response_model=HealthResponseSchema,
    summary="System Health & Model Readiness",
    description="Returns the operational state of the backend and whether neural network weights are loaded.",
)
async def get_health(request: Request) -> HealthResponseSchema:
    """Returns application readiness, model version, and computation device."""
    model_service = getattr(request.app.state, "model_service", None)

    if model_service is not None and model_service.is_loaded:
        info = model_service.get_info()
        return HealthResponseSchema(
            status="ready",
            model_loaded=True,
            model_version=info["model_version"],
            threshold=info["threshold"],
            device=info["device"],
        )

    return HealthResponseSchema(
        status="uninitialized",
        model_loaded=False,
        model_version="Unavailable",
        threshold=None,
        device=None,
    )
