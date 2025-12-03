from typing import Any, Dict, Optional

class AppException(Exception):
    """Base exception for application specific errors"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        payload: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.payload = payload
        super().__init__(self.message)

class FileError(AppException):
    """Errors related to file operations (upload, processing, storage)"""
    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            code="FILE_ERROR",
            payload=payload
        )

class DatabaseError(AppException):
    """Errors related to database operations"""
    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            code="DATABASE_ERROR",
            payload=payload
        )

class ExternalServiceError(AppException):
    """Errors related to external services (OpenAI, GCS, etc)"""
    def __init__(self, message: str, service: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=502,
            code="EXTERNAL_SERVICE_ERROR",
            payload={"service": service, **(payload or {})}
        )

class AuthError(AppException):
    """Authentication and Authorization errors"""
    def __init__(self, message: str, status_code: int = 401, payload: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status_code,
            code="AUTH_ERROR",
            payload=payload
        )

class NotFoundError(AppException):
    """Resource not found errors"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            status_code=404,
            code="NOT_FOUND",
            payload={"resource": resource, "id": resource_id}
        )
