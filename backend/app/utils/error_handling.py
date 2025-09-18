"""
Error Handling Utilities
Comprehensive error handling, retry mechanisms, and circuit breakers
"""

import asyncio
import time
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
import structlog
from enum import Enum

logger = structlog.get_logger()

class RetryStrategy(Enum):
    """Retry strategy types"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered

class RetryConfig:
    """Configuration for retry mechanism"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.strategy = strategy
        self.retryable_exceptions = retryable_exceptions

class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: tuple = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (
            time.time() - self.last_failure_time > self.config.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker closed after successful recovery")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker opened due to failures", 
                          failure_count=self.failure_count)

def retry_with_backoff(config: Optional[RetryConfig] = None):
    """Decorator for retry with exponential backoff"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error("Max retry attempts reached", 
                                   function=func.__name__, 
                                   attempts=config.max_attempts,
                                   error=str(e))
                        raise e
                    
                    delay = _calculate_delay(attempt, config)
                    logger.warning("Retry attempt failed, retrying", 
                                 function=func.__name__,
                                 attempt=attempt + 1,
                                 delay=delay,
                                 error=str(e))
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error("Max retry attempts reached", 
                                   function=func.__name__, 
                                   attempts=config.max_attempts,
                                   error=str(e))
                        raise e
                    
                    delay = _calculate_delay(attempt, config)
                    logger.warning("Retry attempt failed, retrying", 
                                 function=func.__name__,
                                 attempt=attempt + 1,
                                 delay=delay,
                                 error=str(e))
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay based on retry strategy"""
    if config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay * (attempt + 1)
    elif config.strategy == RetryStrategy.EXPONENTIAL:
        delay = config.base_delay * (config.backoff_factor ** attempt)
    else:  # FIXED
        delay = config.base_delay
    
    return min(delay, config.max_delay)

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_database_error(e: Exception, operation: str) -> Dict[str, Any]:
        """Handle database errors"""
        error_info = {
            "operation": operation,
            "error_type": "database_error",
            "error_message": str(e),
            "timestamp": time.time()
        }
        
        if "connection" in str(e).lower():
            error_info["error_code"] = "DB_CONNECTION_ERROR"
            error_info["suggested_action"] = "check_database_connection"
        elif "timeout" in str(e).lower():
            error_info["error_code"] = "DB_TIMEOUT_ERROR"
            error_info["suggested_action"] = "optimize_query_or_increase_timeout"
        elif "constraint" in str(e).lower():
            error_info["error_code"] = "DB_CONSTRAINT_ERROR"
            error_info["suggested_action"] = "check_data_integrity"
        else:
            error_info["error_code"] = "DB_UNKNOWN_ERROR"
            error_info["suggested_action"] = "check_logs_for_details"
        
        logger.error("Database error occurred", **error_info)
        return error_info
    
    @staticmethod
    def handle_api_error(e: Exception, endpoint: str) -> Dict[str, Any]:
        """Handle API errors"""
        error_info = {
            "endpoint": endpoint,
            "error_type": "api_error",
            "error_message": str(e),
            "timestamp": time.time()
        }
        
        if "timeout" in str(e).lower():
            error_info["error_code"] = "API_TIMEOUT_ERROR"
            error_info["suggested_action"] = "increase_timeout_or_retry"
        elif "connection" in str(e).lower():
            error_info["error_code"] = "API_CONNECTION_ERROR"
            error_info["suggested_action"] = "check_network_connectivity"
        elif "rate limit" in str(e).lower():
            error_info["error_code"] = "API_RATE_LIMIT_ERROR"
            error_info["suggested_action"] = "implement_backoff_strategy"
        else:
            error_info["error_code"] = "API_UNKNOWN_ERROR"
            error_info["suggested_action"] = "check_api_documentation"
        
        logger.error("API error occurred", **error_info)
        return error_info
    
    @staticmethod
    def handle_cache_error(e: Exception, operation: str) -> Dict[str, Any]:
        """Handle cache errors"""
        error_info = {
            "operation": operation,
            "error_type": "cache_error",
            "error_message": str(e),
            "timestamp": time.time()
        }
        
        if "connection" in str(e).lower():
            error_info["error_code"] = "CACHE_CONNECTION_ERROR"
            error_info["suggested_action"] = "check_redis_connection"
        elif "timeout" in str(e).lower():
            error_info["error_code"] = "CACHE_TIMEOUT_ERROR"
            error_info["suggested_action"] = "increase_redis_timeout"
        else:
            error_info["error_code"] = "CACHE_UNKNOWN_ERROR"
            error_info["suggested_action"] = "check_redis_logs"
        
        logger.warning("Cache error occurred", **error_info)
        return error_info

class TimeoutManager:
    """Manage operation timeouts"""
    
    @staticmethod
    async def with_timeout(
        coro: Any, 
        timeout: float, 
        timeout_message: str = "Operation timed out"
    ) -> Any:
        """Execute coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error("Operation timed out", timeout=timeout, message=timeout_message)
            raise Exception(timeout_message)

# Global circuit breakers
class GlobalCircuitBreakers:
    """Global circuit breakers for different services"""
    
    def __init__(self):
        self.database_cb = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=30.0
            )
        )
        
        self.external_api_cb = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=60.0
            )
        )
        
        self.cache_cb = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=30.0
            )
        )

# Global instances
global_circuit_breakers = GlobalCircuitBreakers()
error_handler = ErrorHandler()
