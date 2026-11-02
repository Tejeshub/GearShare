import logging
from typing import Literal
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        503: {
            "model": HealthResponse,
            "description": "Database or service unavailable",
        }
    },
    summary="Health check endpoint",
    description="Validates API runtime health and checks database connectivity.",
)
def check_health(db: Session = Depends(get_db)):
    try:
        # Perform lightweight connectivity check
        db.execute(text("SELECT 1"))
        return HealthResponse(status="healthy", database="connected")
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(status="unhealthy", database="disconnected").model_dump(),
        )
