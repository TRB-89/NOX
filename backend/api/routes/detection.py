"""
NØX - Intrusion Detection Routes
Endpoints for single-flow inference, batch detection, CSV dataset upload, and telemetry stats.
"""

from typing import List
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from backend.api.schemas.detection_schema import (
    FlowRecordSchema,
    DetectionResponseSchema,
    BatchDetectionRequest,
    CSVUploadResponseSchema,
    TelemetryStatsSchema,
)

router = APIRouter(prefix="/api", tags=["Intrusion Detection"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB upload limit


@router.post(
    "/detect",
    response_model=DetectionResponseSchema,
    summary="Detect Intrusion (Single Flow)",
    description="Analyzes one raw network traffic flow record, applies preprocessing, and runs neural inference.",
)
async def detect_single(record: FlowRecordSchema, request: Request) -> DetectionResponseSchema:
    detection_service = getattr(request.app.state, "detection_service", None)
    if not detection_service or not detection_service.model_service.is_loaded:
        raise HTTPException(status_code=503, detail="Neural detection engine is not loaded.")

    try:
        data = record.model_dump()
        result = detection_service.detect_single(data, source_type="single")
        return DetectionResponseSchema(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference failure: {str(e)}")


@router.post(
    "/detect/batch",
    response_model=List[DetectionResponseSchema],
    summary="Detect Intrusions (Batch)",
    description="Processes up to 5,000 network traffic flow records in order.",
)
async def detect_batch(batch_req: BatchDetectionRequest, request: Request) -> List[DetectionResponseSchema]:
    detection_service = getattr(request.app.state, "detection_service", None)
    if not detection_service or not detection_service.model_service.is_loaded:
        raise HTTPException(status_code=503, detail="Neural detection engine is not loaded.")

    try:
        records_data = [r.model_dump() for r in batch_req.records]
        results = detection_service.detect_batch(records_data, source_type="batch")
        return [DetectionResponseSchema(**res) for res in results]
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")


@router.post(
    "/detect/upload",
    response_model=CSVUploadResponseSchema,
    summary="Analyze Uploaded Network Traffic CSV",
    description="Streams an uploaded CSV dataset in bounded memory chunks, executes neural classification, and logs events.",
)
async def detect_upload(
    request: Request,
    file: UploadFile = File(..., description="UNSW-NB15 compatible CSV network traffic file"),
) -> CSVUploadResponseSchema:
    detection_service = getattr(request.app.state, "detection_service", None)
    if not detection_service or not detection_service.model_service.is_loaded:
        raise HTTPException(status_code=503, detail="Neural detection engine is not loaded.")

    # 1. Validate file extension
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .csv files are supported.")

    # 2. Read bytes with size protection
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_BYTES // (1024*1024)} MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = detection_service.process_csv_upload(contents)
        return CSVUploadResponseSchema(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")


@router.get(
    "/stats",
    response_model=TelemetryStatsSchema,
    summary="Dashboard Telemetry Statistics",
    description="Returns live statistics aggregated from stored SQLite detection events.",
)
async def get_stats(request: Request) -> TelemetryStatsSchema:
    event_dao = getattr(request.app.state, "event_dao", None)
    if not event_dao:
        raise HTTPException(status_code=503, detail="Database service uninitialized.")

    stats = event_dao.get_telemetry_stats()
    return TelemetryStatsSchema(**stats)
