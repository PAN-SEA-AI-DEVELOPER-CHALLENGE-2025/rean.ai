"""
Custom exception classes for the Pan-Sea Backend application.
"""
from typing import Any, Dict, Optional


class PanSeaException(Exception):
    """Base exception class for Pan-Sea application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(PanSeaException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(PanSeaException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class ValidationError(PanSeaException):
    """Data validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class NotFoundError(PanSeaException):
    """Resource not found errors"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class ConflictError(PanSeaException):
    """Resource conflict errors"""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)


class DatabaseError(PanSeaException):
    """Database operation errors"""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ExternalServiceError(PanSeaException):
    """External service errors (AI, S3, etc.)"""
    
    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, details=details)


class RateLimitError(PanSeaException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, details=details)


class FileProcessingError(PanSeaException):
    """File processing related errors"""
    
    def __init__(self, message: str = "File processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)
