"""
Health Monitor Service
System health monitoring and observability
"""

import asyncio
import psutil
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import structlog
from ..services.cache_manager import cache_manager
from ..db_utils.optimization import db_optimizer
from ..core.config import get_settings

logger = structlog.get_logger()

class HealthCheck:
    """Individual health check"""
    
    def __init__(self, name: str, check_func, critical: bool = True):
        self.name = name
        self.check_func = check_func
        self.critical = critical
        self.last_check = None
        self.last_result = None
        self.last_error = None
    
    async def run_check(self) -> Dict[str, Any]:
        """Run the health check"""
        try:
            start_time = time.time()
            result = await self.check_func() if asyncio.iscoroutinefunction(self.check_func) else self.check_func()
            duration = time.time() - start_time
            
            self.last_check = datetime.now(timezone.utc)
            self.last_result = {
                "status": "healthy",
                "duration": duration,
                "result": result
            }
            self.last_error = None
            
            return self.last_result
            
        except Exception as e:
            duration = time.time() - start_time
            self.last_check = datetime.now(timezone.utc)
            self.last_result = {
                "status": "unhealthy",
                "duration": duration,
                "error": str(e)
            }
            self.last_error = e
            
            logger.error("Health check failed", check_name=self.name, error=str(e))
            return self.last_result

class HealthMonitor:
    """System health monitoring service"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.monitoring_active = False
        self.check_interval = 30  # seconds
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        # Initialize health checks
        self._initialize_health_checks()
    
    def _initialize_health_checks(self):
        """Initialize all health checks"""
        # Database health check
        self.add_check("database", self._check_database_health, critical=True)
        
        # Cache health check
        self.add_check("cache", self._check_cache_health, critical=False)
        
        # Disk space check
        self.add_check("disk_space", self._check_disk_space, critical=True)
        
        # Memory usage check
        self.add_check("memory", self._check_memory_usage, critical=True)
        
        # CPU usage check
        self.add_check("cpu", self._check_cpu_usage, critical=False)
        
        # Network connectivity check
        self.add_check("network", self._check_network_connectivity, critical=False)
        
        # External services check
        self.add_check("external_apis", self._check_external_apis, critical=False)
    
    def add_check(self, name: str, check_func, critical: bool = True):
        """Add a health check"""
        self.checks[name] = HealthCheck(name, check_func, critical)
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Test database connection
            start_time = time.time()
            
            # Get database stats
            stats = db_optimizer.get_database_stats()
            
            # Check connection pool
            if db_optimizer.engine:
                with db_optimizer.engine.connect() as conn:
                    conn.execute("SELECT 1")
            
            duration = time.time() - start_time
            
            return {
                "connection_ok": True,
                "response_time": duration,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "connection_ok": False,
                "error": str(e)
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health"""
        try:
            if not cache_manager.redis_client:
                await cache_manager.connect()
            
            # Test cache connection
            start_time = time.time()
            await cache_manager.set("health_check", "test", ttl=10)
            test_value = await cache_manager.get("health_check")
            duration = time.time() - start_time
            
            # Get cache stats
            stats = await cache_manager.get_cache_stats()
            
            return {
                "connection_ok": test_value == "test",
                "response_time": duration,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "connection_ok": False,
                "error": str(e)
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            total_gb = disk_usage.total / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Alert if usage > 90%
            status = "warning" if usage_percent > 90 else "healthy"
            
            return {
                "total_gb": round(total_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_gb": round(used_gb, 2),
                "usage_percent": round(usage_percent, 2),
                "status": status
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            used_gb = memory.used / (1024**3)
            usage_percent = memory.percent
            
            # Alert if usage > 85%
            status = "warning" if usage_percent > 85 else "healthy"
            
            return {
                "total_gb": round(total_gb, 2),
                "available_gb": round(available_gb, 2),
                "used_gb": round(used_gb, 2),
                "usage_percent": round(usage_percent, 2),
                "status": status
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            # Get CPU usage over 5 seconds
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Alert if usage > 80%
            status = "warning" if cpu_percent > 80 else "healthy"
            
            return {
                "usage_percent": round(cpu_percent, 2),
                "cpu_count": cpu_count,
                "status": status
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            import socket
            
            # Test DNS resolution
            start_time = time.time()
            socket.gethostbyname("google.com")
            dns_time = time.time() - start_time
            
            return {
                "dns_resolution": True,
                "dns_time": round(dns_time, 3),
                "status": "healthy"
            }
            
        except Exception as e:
            return {
                "dns_resolution": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        try:
            import aiohttp
            
            api_status = {}
            
            # Check VirusTotal API
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://www.virustotal.com/api/v3/status", timeout=5) as response:
                        api_status["virustotal"] = {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "response_code": response.status
                        }
            except Exception as e:
                api_status["virustotal"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check other APIs as needed
            # api_status["google_safe_browsing"] = await self._check_google_safe_browsing()
            # api_status["phish_tank"] = await self._check_phish_tank()
            
            overall_status = "healthy" if all(
                api.get("status") == "healthy" for api in api_status.values()
            ) else "degraded"
            
            return {
                "apis": api_status,
                "overall_status": overall_status
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        try:
            results = {}
            overall_status = "healthy"
            critical_failures = 0
            
            # Run all checks concurrently
            check_tasks = []
            for check_name, check in self.checks.items():
                check_tasks.append(check.run_check())
            
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            # Process results
            for i, (check_name, check) in enumerate(self.checks.items()):
                result = check_results[i]
                if isinstance(result, Exception):
                    result = {"status": "unhealthy", "error": str(result)}
                
                results[check_name] = result
                
                if result.get("status") == "unhealthy":
                    if check.critical:
                        critical_failures += 1
                        overall_status = "critical"
                    elif overall_status == "healthy":
                        overall_status = "degraded"
            
            # Create summary
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": overall_status,
                "critical_failures": critical_failures,
                "total_checks": len(self.checks),
                "healthy_checks": sum(1 for r in results.values() if r.get("status") in ["healthy", "warning"]),
                "results": results
            }
            
            # Store in history
            self.metrics_history.append(summary)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]
            
            return summary
            
        except Exception as e:
            logger.error("Failed to run health checks", error=str(e))
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": "critical",
                "error": str(e)
            }
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        logger.info("Starting health monitoring", interval=self.check_interval)
        
        while self.monitoring_active:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("Stopped health monitoring")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest = self.metrics_history[-1]
        return latest
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over time"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
            ]
            
            if not recent_metrics:
                return {"error": "no_data_in_timeframe"}
            
            # Calculate trends
            trends = {
                "timeframe_hours": hours,
                "total_checks": len(recent_metrics),
                "health_percentage": sum(1 for m in recent_metrics if m["overall_status"] == "healthy") / len(recent_metrics) * 100,
                "critical_incidents": sum(1 for m in recent_metrics if m["overall_status"] == "critical"),
                "degraded_periods": sum(1 for m in recent_metrics if m["overall_status"] == "degraded"),
                "average_response_times": {}
            }
            
            # Calculate average response times for each check
            for check_name in self.checks.keys():
                response_times = [
                    m["results"][check_name].get("duration", 0)
                    for m in recent_metrics
                    if check_name in m["results"] and "duration" in m["results"][check_name]
                ]
                if response_times:
                    trends["average_response_times"][check_name] = round(sum(response_times) / len(response_times), 3)
            
            return trends
            
        except Exception as e:
            logger.error("Failed to calculate health trends", error=str(e))
            return {"error": str(e)}

# Global health monitor instance
health_monitor = HealthMonitor()
