"""
NØX - Neural Network Intrusion Detection System
FastAPI Backend Application (Module 03)

Exposes RESTful endpoints for real-time intrusion detection, batch classification,
bounded CSV upload analysis, live SQLite threat event logging, and dashboard telemetry.
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.database.db import init_db
from backend.database.models import DetectionEventDAO
from backend.services.model_service import ModelService
from backend.services.detection_service import DetectionService
from backend.api.routes.health import router as health_router
from backend.api.routes.detection import router as detection_router
from backend.api.routes.history import router as history_router

# Configure backend logging
logs_dir = Path(__file__).resolve().parent.parent / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logs_dir / "nox_backend.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("NOX.API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager:
    Initializes SQLite schema and loads PyTorch model & preprocessing pipeline
    once during application startup.
    """
    logger.info("Initializing NØX database schema...")
    init_db()

    logger.info("Loading PyTorch model & preprocessing pipeline into memory...")
    model_service = ModelService()
    try:
        model_service.load_artifacts()
    except Exception as e:
        logger.error("Failed to load model artifacts during startup: %s", e, exc_info=True)

    event_dao = DetectionEventDAO()
    detection_service = DetectionService(model_service=model_service, event_dao=event_dao)

    # Attach to app.state for request dependency access
    app.state.model_service = model_service
    app.state.event_dao = event_dao
    app.state.detection_service = detection_service

    logger.info("NØX Intrusion Detection Backend is READY. Listening on local interface.")
    yield
    logger.info("NØX Backend is shutting down gracefully.")


app = FastAPI(
    title="NØX — Neural Network Intrusion Detection System",
    description=(
        "Industrial Cybersecurity Telemetry & Deep Learning Intrusion Detection API. "
        "Provides real-time packet flow classification, batch processing, CSV upload telemetry, "
        "threat severity categorization, and SQLite event persistence."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration restricted to local development frontend origins
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(detection_router)
app.include_router(history_router)


@app.get("/", tags=["Root"], summary="NØX Backend Root")
async def root():
    """Root entrypoint linking to interactive documentation."""
    return {
        "system": "NØX — Neural Network Intrusion Detection System",
        "module": "Module 03: FastAPI Backend & Threat Logging",
        "documentation": "/docs",
        "health": "/api/health",
        "status": "operational",
    }


# Structured Exception Handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors cleanly without exposing internals."""
    logger.warning("Input validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The submitted network traffic parameters failed schema validation.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server errors safely."""
    logger.error("Unhandled exception on %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing network traffic telemetry.",
        },
    )


if __name__ == "__main__":
    import uvicorn
    # Bind strictly to local loopback interface for local dev security
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)
