"""
NØX - Historical Telemetry Routes
Returns paginated detection records and security incident logs from SQLite.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, Query, HTTPException

router = APIRouter(prefix="/api", tags=["Threat History"])


@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="Detection Event History",
    description="Returns paginated historical intrusion detection records logged by the system.",
)
async def get_history(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Maximum records to return (1-500)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    source_type: Optional[str] = Query(None, description="Filter by source (single, batch, csv_upload, demo)"),
) -> List[Dict[str, Any]]:
    event_dao = getattr(request.app.state, "event_dao", None)
    if not event_dao:
        raise HTTPException(status_code=503, detail="Database service uninitialized.")

    try:
        events = event_dao.get_recent_history(limit=limit, offset=offset, source_type=source_type)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")
