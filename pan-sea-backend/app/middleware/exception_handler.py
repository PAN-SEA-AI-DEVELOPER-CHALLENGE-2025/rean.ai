"""
Global exception handler middleware for consistent error responses.
"""
import logging
from typing import Any, Dict

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import PanSeaException

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally and return consistent error responses"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except PanSeaException as exc:
            logger.error(f"PanSea exception: {exc.message}", extra={
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method
            })
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "message": exc.message,
                        "details": exc.details,
                        "type": exc.__class__.__name__
                    }
                }
            )
        except HTTPException as exc:
            logger.error(f"HTTP exception: {exc.detail}", extra={
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method
            })
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "message": exc.detail,
                        "type": "HTTPException"
                    }
                }
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {str(exc)}", extra={
                "path": request.url.path,
                "method": request.method
            }, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal server error",
                        "type": "InternalServerError"
                    }
                }
            )


def format_error_response(message: str, details: Dict[str, Any] = None, error_type: str = "Error") -> Dict[str, Any]:
    """Format a consistent error response"""
    return {
        "error": {
            "message": message,
            "details": details or {},
            "type": error_type
        }
    }
