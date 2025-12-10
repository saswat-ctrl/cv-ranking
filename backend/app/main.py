import time
import uuid
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.api.v1 import api_router
from app.core.exceptions import AppException
from app.core.logging import configure_logging

# Configure logging immediately
configure_logging(log_level=settings.LOG_LEVEL, json_format=settings.LOG_JSON_FORMAT)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API for CV Ranking MVP",
    version="0.1.0",
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "request_processed",
            http_method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=process_time,
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "request_failed",
            http_method=request.method,
            url=str(request.url),
            duration=process_time,
            exc_info=True,
        )
        raise e

# Global Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "code": exc.code,
            "payload": exc.payload
        },
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "HTTP_ERROR",
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "code": "VALIDATION_ERROR",
            "errors": exc.errors()
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    import traceback
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # Print to console for debugging
    print(f"\n{'='*80}")
    print(f"UNHANDLED EXCEPTION in {request.method} {request.url.path}")
    print(f"Exception type: {type(exc).__name__}")
    print(f"Exception message: {exc}")
    print(f"Traceback:")
    traceback.print_exc()
    print(f"{'='*80}\n")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "code": "INTERNAL_ERROR",
        },
    )

# Set all CORS enabled origins
# NOTE:
# - We avoid using ["*"] together with allow_credentials=True because some browsers
#   will then drop CORS headers, which can surface as generic "Network Error" /
#   CORS failures on the frontend.
# - Instead, we explicitly list the frontend origin(s) we want to allow.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).rstrip('/') for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, status, HTTPException
from app.api import deps

@app.get("/health")
async def health_check(db: AsyncSession = Depends(deps.get_db)):
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
