"""
Security headers middleware for enhanced security.
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Scope, Receive, Send
from app.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy (basic)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            
            # Permissions Policy
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "interest-cohort=(), payment=(), usb=()"
            ),

            # Cross-Origin protections
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            
            # Remove server information
            "Server": "",
        }
    
    async def dispatch(self, request: Scope, call_next: Receive) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            if header == "Server":
                # Remove server header by not setting it
                continue
            response.headers[header] = value
        
        # Relax CSP for documentation pages to allow inline scripts needed by Swagger/ReDoc
        try:
            path = request.url.path  # Request instance
        except AttributeError:
            path = request.get("path", "/") if isinstance(request, dict) else "/"
        
        if path in ("/docs", "/redoc"):
            base_csp = self.security_headers["Content-Security-Policy"]
            docs_csp = base_csp.replace(
                "script-src 'self' https://cdn.jsdelivr.net;",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
            )
            response.headers["Content-Security-Policy"] = docs_csp
        
        # Add HSTS header in non-debug mode
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response
