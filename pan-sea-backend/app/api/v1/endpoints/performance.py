"""
Performance monitoring and health check endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import asyncio
import time
from app.core.dependencies import require_admin
from app.core.cache import cache_service
from app.utils.file_optimization import memory_optimizer
from app.database.database import db_manager

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "pan-sea-backend"
    }


@router.get("/performance", response_model=Dict[str, Any])
async def performance_metrics(current_admin: dict = Depends(require_admin)):
    """Get performance metrics (Admin only)"""
    try:
        # Memory usage
        memory_info = memory_optimizer.get_memory_usage()
        
        # Cache status
        cache_status = "connected" if cache_service.redis_client else "disconnected"
        
        # Database connection test
        db_status = "connected"
        try:
            await db_manager.execute_query("SELECT 1")
        except Exception:
            db_status = "disconnected"
        
        return {
            "memory": memory_info,
            "cache": {
                "status": cache_status,
                "redis_url": cache_service.redis_url
            },
            "database": {
                "status": db_status
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")


@router.post("/performance/cleanup", response_model=Dict[str, Any])
async def cleanup_resources(current_admin: dict = Depends(require_admin)):
    """Cleanup system resources (Admin only)"""
    try:
        # Force memory cleanup
        await memory_optimizer.cleanup_memory()
        
        # Clear cache (optional - be careful in production)
        if cache_service.redis_client:
            # Only clear non-critical cache
            await cache_service.delete_pattern("temp:*")
        
        return {
            "message": "System cleanup completed",
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


@router.get("/performance/cache/stats", response_model=Dict[str, Any])
async def cache_stats(current_admin: dict = Depends(require_admin)):
    """Get cache statistics (Admin only)"""
    try:
        if not cache_service.redis_client:
            return {"error": "Cache not connected"}
        
        # Get Redis info
        info = await cache_service.redis_client.info()
        
        return {
            "redis_info": {
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")


@router.post("/performance/cache/clear", response_model=Dict[str, Any])
async def clear_cache(current_admin: dict = Depends(require_admin)):
    """Clear all cache (Admin only - use with caution)"""
    try:
        if not cache_service.redis_client:
            return {"error": "Cache not connected"}
        
        # Clear all cache
        await cache_service.redis_client.flushdb()
        
        return {
            "message": "Cache cleared successfully",
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
