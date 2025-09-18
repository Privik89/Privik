"""
Cache Manager Service
Handles Redis caching for improved performance
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
import structlog
import redis.asyncio as redis
from ..core.config import settings

logger = structlog.get_logger()

class CacheManager:
    """Manages Redis caching for improved performance"""
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 hour default TTL
        
    async def connect(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """Set a value in cache with optional TTL"""
        try:
            if not self.redis_client:
                return False
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Add namespace
            cache_key = f"{namespace}:{key}"
            
            # Set with TTL
            ttl = ttl or self.default_ttl
            await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            logger.debug("Cache set", key=cache_key, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False
    
    async def get(
        self, 
        key: str, 
        namespace: str = "default",
        default: Any = None
    ) -> Any:
        """Get a value from cache"""
        try:
            if not self.redis_client:
                return default
            
            cache_key = f"{namespace}:{key}"
            value = await self.redis_client.get(cache_key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return default
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete a value from cache"""
        try:
            if not self.redis_client:
                return False
            
            cache_key = f"{namespace}:{key}"
            result = await self.redis_client.delete(cache_key)
            
            logger.debug("Cache delete", key=cache_key, result=bool(result))
            return bool(result)
            
        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if a key exists in cache"""
        try:
            if not self.redis_client:
                return False
            
            cache_key = f"{namespace}:{key}"
            result = await self.redis_client.exists(cache_key)
            
            return bool(result)
            
        except Exception as e:
            logger.error("Cache exists check failed", key=key, error=str(e))
            return False
    
    async def get_or_set(
        self,
        key: str,
        factory_func,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> Any:
        """Get value from cache or set it using factory function"""
        try:
            # Try to get from cache first
            cached_value = await self.get(key, namespace)
            if cached_value is not None:
                return cached_value
            
            # Generate new value
            new_value = await factory_func() if asyncio.iscoroutinefunction(factory_func) else factory_func()
            
            # Cache the new value
            await self.set(key, new_value, ttl, namespace)
            
            return new_value
            
        except Exception as e:
            logger.error("Cache get_or_set failed", key=key, error=str(e))
            # Fallback to factory function
            return await factory_func() if asyncio.iscoroutinefunction(factory_func) else factory_func()
    
    async def increment(self, key: str, amount: int = 1, namespace: str = "default") -> Optional[int]:
        """Increment a numeric value in cache"""
        try:
            if not self.redis_client:
                return None
            
            cache_key = f"{namespace}:{key}"
            result = await self.redis_client.incrby(cache_key, amount)
            
            return result
            
        except Exception as e:
            logger.error("Cache increment failed", key=key, error=str(e))
            return None
    
    async def expire(self, key: str, ttl: int, namespace: str = "default") -> bool:
        """Set expiration for a key"""
        try:
            if not self.redis_client:
                return False
            
            cache_key = f"{namespace}:{key}"
            result = await self.redis_client.expire(cache_key, ttl)
            
            return bool(result)
            
        except Exception as e:
            logger.error("Cache expire failed", key=key, error=str(e))
            return False
    
    async def flush_namespace(self, namespace: str = "default") -> bool:
        """Flush all keys in a namespace"""
        try:
            if not self.redis_client:
                return False
            
            pattern = f"{namespace}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Flushed namespace", namespace=namespace, key_count=len(keys))
            
            return True
            
        except Exception as e:
            logger.error("Cache flush namespace failed", namespace=namespace, error=str(e))
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not self.redis_client:
                return {"error": "Redis not connected"}
            
            info = await self.redis_client.info()
            
            stats = {
                "connected": True,
                "used_memory": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": 0
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            
            if total > 0:
                stats["hit_rate"] = round((hits / total) * 100, 2)
            
            return stats
            
        except Exception as e:
            logger.error("Error getting cache stats", error=str(e))
            return {"error": str(e)}

# Cache namespaces
class CacheNamespaces:
    EMAIL_ANALYSIS = "email_analysis"
    DOMAIN_REPUTATION = "domain_reputation"
    THREAT_INTEL = "threat_intel"
    USER_SESSIONS = "user_sessions"
    API_RATE_LIMIT = "rate_limit"
    STATISTICS = "statistics"
    SANDBOX_RESULTS = "sandbox_results"
    INCIDENT_CACHE = "incident_cache"

# Global cache manager instance
cache_manager = CacheManager()
