from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1.endpoints import auth, jobs, downloads, health
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(downloads.router, prefix="/downloads", tags=["downloads"])
api_router.include_router(health.router, tags=["health"])
