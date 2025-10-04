"""
Input validation and sanitization utilities for security.
"""
import re
import html
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class InputValidator:
    """Utility class for input validation and sanitization"""
    
    # Common patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{10,20}$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%^&*()+=\[\]{}|\\:";\'<>?/~`]*$')
    
    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+\w+\s*=\s*\w+)',
        r'(\bUNION\s+SELECT\b)',
        r'(\bDROP\s+TABLE\b)',
        r'(\bDELETE\s+FROM\b)',
        r'(\bINSERT\s+INTO\b)',
        r'(\bUPDATE\s+SET\b)',
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and sanitize email address"""
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        email = email.strip().lower()
        
        if not cls.EMAIL_PATTERN.match(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        if len(email) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email too long"
            )
        
        return email
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Validate and sanitize username"""
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is required"
            )
        
        username = username.strip()
        
        if not cls.USERNAME_PATTERN.match(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be 3-30 characters, alphanumeric with _ or - only"
            )
        
        return username
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Validate password strength"""
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        if len(password) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too long"
            )
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in weak_passwords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too common, please choose a stronger password"
            )
        
        return password
    
    @classmethod
    def validate_phone(cls, phone: Optional[str]) -> Optional[str]:
        """Validate and sanitize phone number"""
        if not phone:
            return None
        
        phone = phone.strip()
        
        if not cls.PHONE_PATTERN.match(phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        return phone
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS and other attacks"""
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        # Check for dangerous patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input contains potentially dangerous content"
                )
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input contains potentially dangerous content"
                )
        
        return text
    
    @classmethod
    def validate_file_upload(cls, filename: str, content_type: str, file_size: int) -> Dict[str, Any]:
        """Validate file upload parameters"""
        # Check file extension
        allowed_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Check content type
        if not content_type or not content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 10MB"
            )
        
        # Sanitize filename
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        return {
            "safe_filename": safe_filename,
            "file_extension": file_ext,
            "content_type": content_type,
            "file_size": file_size
        }
    
    @classmethod
    def validate_pagination(cls, skip: int, limit: int) -> Dict[str, int]:
        """Validate pagination parameters"""
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip parameter must be non-negative"
            )
        
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        return {"skip": skip, "limit": limit}
    
    @classmethod
    def validate_uuid(cls, uuid_string: str, field_name: str = "ID") -> str:
        """Validate UUID format"""
        if not uuid_string:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required"
            )
        
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(uuid_string):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )
        
        return uuid_string


# Global validator instance
input_validator = InputValidator()
