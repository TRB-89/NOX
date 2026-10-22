"""
NØX - API Routes Package
"""

from backend.api.routes.health import router as health_router
from backend.api.routes.detection import router as detection_router
from backend.api.routes.history import router as history_router

__all__ = ["health_router", "detection_router", "history_router"]
