"""
Performance API Router
Health monitoring, performance metrics, and system status endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.health_monitor import health_monitor
from ..services.cache_manager import cache_manager
from ..db_utils.optimization import db_optimizer
from ..services.logging_service import logging_service
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/health")
async def health_check(
    _: dict = Depends(verify_request)
):
    """Get system health status"""
    try:
        health_summary = await health_monitor.run_all_checks()
        return health_summary
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/health/summary")
async def health_summary(
    _: dict = Depends(verify_request)
):
    """Get current health summary"""
    try:
        summary = health_monitor.get_health_summary()
        return summary
        
    except Exception as e:
        logger.error("Failed to get health summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get health summary")

@router.get("/health/trends")
async def health_trends(
    hours: int = 24,
    _: dict = Depends(verify_request)
):
    """Get health trends over time"""
    try:
        trends = health_monitor.get_health_trends(hours=hours)
        return trends
        
    except Exception as e:
        logger.error("Failed to get health trends", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get health trends")

@router.get("/performance/cache")
async def cache_performance(
    _: dict = Depends(verify_request)
):
    """Get cache performance metrics"""
    try:
        stats = await cache_manager.get_cache_stats()
        return stats
        
    except Exception as e:
        logger.error("Failed to get cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get cache stats")

@router.get("/performance/database")
async def database_performance(
    _: dict = Depends(verify_request)
):
    """Get database performance metrics"""
    try:
        stats = db_optimizer.get_database_stats()
        return stats
        
    except Exception as e:
        logger.error("Failed to get database stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get database stats")

@router.get("/performance/logs")
async def logging_performance(
    _: dict = Depends(verify_request)
):
    """Get logging system metrics"""
    try:
        metrics = await logging_service.get_system_metrics()
        return metrics
        
    except Exception as e:
        logger.error("Failed to get logging metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get logging metrics")

@router.post("/performance/cache/flush")
async def flush_cache(
    namespace: Optional[str] = None,
    _: dict = Depends(verify_request)
):
    """Flush cache or specific namespace"""
    try:
        if namespace:
            result = await cache_manager.flush_namespace(namespace)
        else:
            # Flush all namespaces
            namespaces = [
                "email_analysis",
                "domain_reputation", 
                "threat_intel",
                "user_sessions",
                "rate_limit",
                "statistics",
                "sandbox_results",
                "incident_cache"
            ]
            results = []
            for ns in namespaces:
                result = await cache_manager.flush_namespace(ns)
                results.append({"namespace": ns, "success": result})
            
            return {"message": "Cache flush completed", "results": results}
        
        return {"message": f"Cache flush completed for namespace: {namespace}", "success": result}
        
    except Exception as e:
        logger.error("Failed to flush cache", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to flush cache")

@router.post("/performance/database/optimize")
async def optimize_database(
    _: dict = Depends(verify_request)
):
    """Optimize database performance"""
    try:
        # Create performance indexes
        db_optimizer.create_performance_indexes()
        
        # Optimize database settings
        db_optimizer.optimize_database_settings()
        
        # Analyze query performance
        db_optimizer.analyze_query_performance()
        
        return {"message": "Database optimization completed"}
        
    except Exception as e:
        logger.error("Database optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail="Database optimization failed")

@router.get("/performance/system")
async def system_performance(
    _: dict = Depends(verify_request)
):
    """Get overall system performance metrics"""
    try:
        import psutil
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        system_metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "usage_percent": round((disk.used / disk.total) * 100, 2)
            },
            "process": {
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            }
        }
        
        return system_metrics
        
    except Exception as e:
        logger.error("Failed to get system performance", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system performance")

@router.get("/performance/status")
async def performance_status(
    _: dict = Depends(verify_request)
):
    """Get comprehensive performance status"""
    try:
        # Get all performance metrics
        health_summary = health_monitor.get_health_summary()
        cache_stats = await cache_manager.get_cache_stats()
        db_stats = db_optimizer.get_database_stats()
        log_metrics = await logging_service.get_system_metrics()
        
        # Determine overall status
        overall_status = "healthy"
        if health_summary.get("overall_status") == "critical":
            overall_status = "critical"
        elif health_summary.get("overall_status") == "degraded":
            overall_status = "degraded"
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "health": health_summary,
            "cache": cache_stats,
            "database": db_stats,
            "logging": log_metrics
        }
        
    except Exception as e:
        logger.error("Failed to get performance status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get performance status")
