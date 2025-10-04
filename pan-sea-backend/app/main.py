from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from app.config import settings
from app.api.v1.api import api_v1_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.exception_handler import ExceptionHandlerMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.core.cache import cache_service
from app.services.rag_service import rag_service
from app.database.database import db_manager
from sqlalchemy import text
import asyncio
from starlette.middleware.trustedhost import TrustedHostMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    await cache_service.connect()
    # Start indexing worker
    await rag_service.indexer.start_worker()
    # Schedule periodic ANALYZE (lightweight)
    async def analyze_periodically():
        while True:
            try:
                async with db_manager.async_engine.begin() as conn:
                    await conn.execute(text("ANALYZE"))
            except Exception:
                pass
            await asyncio.sleep(6 * 60 * 60)
    app.state._analyze_task = asyncio.create_task(analyze_periodically())
    yield
    # Shutdown
    await cache_service.disconnect()
    # Stop indexing worker
    try:
        await rag_service.indexer.stop_worker()
    except Exception:
        pass
    # Cancel analyze task
    try:
        app.state._analyze_task.cancel()
    except Exception:
        pass


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
        description="Backend API for Pan-Sea Class Teaching Summarization System",
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware (order matters - first added is outermost)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include API routes
    app.include_router(api_v1_router, prefix="/api/v1")
    
    # Serve static files
    if not os.path.exists(settings.upload_dir):
        os.makedirs(settings.upload_dir)
    
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
    
    # Serve HTML at root path
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        """Serve the main HTML page at the root path"""
        html_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    return app


# Create the FastAPI application
app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
