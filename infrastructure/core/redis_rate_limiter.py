import os
import time
import redis
from typing import Optional
from infrastructure.core.safety import SecureLogger

class RedisRateLimiter:
    """
    Rate limiter implementation using Redis for distributed environments.
    Suitable for Render with multiple workers.
    """
    
    def __init__(self, requests: int = 5, window: int = 60, redis_url: Optional[str] = None):
        self.requests = requests
        self.window = window
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self._connect_redis()
    
    def _connect_redis(self):
        """Establish connection to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
                retry_on_timeout=False
            )
            # Test connection
            self.redis_client.ping()
            SecureLogger.safe_log("Redis connection established for rate limiting")
        except Exception as e:
            SecureLogger.safe_log(f"Failed to connect to Redis: {str(e)}")
            raise ConnectionError("Could not connect to Redis for rate limiting")
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if the request is allowed based on rate limit.
        
        Args:
            key: Unique identifier (typically IP address)
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        try:
            current_time = time.time()
            window_start = current_time - self.window
            
            # Redis key for this IP
            redis_key = f"rate_limit:{key}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(redis_key)
            
            # Unique member per request to avoid same-second deduplication
            pipe.zadd(redis_key, {str(time.time_ns()): current_time})
            
            # Set expiration to clean up old keys
            pipe.expire(redis_key, self.window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            # Check if under limit
            if current_requests < self.requests:
                return True
            else:
                # Remove the request we just added since it exceeded limit
                self.redis_client.zrem(redis_key, str(current_time))
                return False
                
        except Exception as e:
            SecureLogger.safe_log(f"Rate limiter error: {str(e)}")
            # Fail open - allow request if Redis fails
            return True
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the current window"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window
            redis_key = f"rate_limit:{key}"
            
            # Clean old entries and count current
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            results = pipe.execute()
            
            current_requests = results[1]
            remaining = max(0, self.requests - current_requests)
            return remaining
            
        except Exception as e:
            SecureLogger.safe_log(f"Error getting remaining requests: {str(e)}")
            return self.requests  # Assume full limit on error
    
    def reset_limit(self, key: str):
        """Reset rate limit for a specific key"""
        try:
            redis_key = f"rate_limit:{key}"
            self.redis_client.delete(redis_key)
            SecureLogger.safe_log(f"Rate limit reset for key: {key}")
        except Exception as e:
            SecureLogger.safe_log(f"Error resetting rate limit: {str(e)}")

# Fallback to in-memory rate limiter if Redis is not available
class FallbackRateLimiter:
    """Fallback in-memory rate limiter when Redis is unavailable"""
    
    def __init__(self, requests=5, window=60):
        self.requests = requests
        self.window = window
        self.hits = {}
    
    def is_allowed(self, key):
        now = time.time()
        if key not in self.hits:
            self.hits[key] = []
        
        self.hits[key] = [t for t in self.hits[key] if now - t < self.window]
        
        if len(self.hits[key]) < self.requests:
            self.hits[key].append(now)
            return True
        return False
    
    def get_remaining_requests(self, key):
        now = time.time()
        if key not in self.hits:
            return self.requests
        
        self.hits[key] = [t for t in self.hits[key] if now - t < self.window]
        return max(0, self.requests - len(self.hits[key]))
    
    def reset_limit(self, key):
        if key in self.hits:
            del self.hits[key]

def get_rate_limiter(requests=5, window=60) -> RedisRateLimiter | FallbackRateLimiter:
    """
    Factory function to get appropriate rate limiter.
    Tries Redis first, falls back to in-memory if Redis fails.
    """
    try:
        return RedisRateLimiter(requests, window)
    except ConnectionError:
        SecureLogger.safe_log("Using fallback in-memory rate limiter")
        return FallbackRateLimiter(requests, window)
