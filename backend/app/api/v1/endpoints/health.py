from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api import deps
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.get("/health", response_model=Any)
async def health_check(db: AsyncSession = Depends(deps.get_db)) :
    """
    Health check endpoint.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "version": "0.1.0", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
