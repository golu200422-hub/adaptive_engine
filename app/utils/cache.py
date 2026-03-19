# ============================================================
# app/utils/cache.py
# Redis Cache with In-Memory Fallback
#
# What is Redis?
# Redis is like a super-fast notepad that your computer keeps
# in its memory (RAM) instead of on disk.
# Reading from RAM is 1000x faster than reading from a file!
#
# Example use case:
# Instead of asking the database "what's the difficulty for session ABC?"
# every single time, we remember it in Redis for quick access.
#
# DON'T WORRY if you don't have Redis installed!
# This file automatically falls back to a simple Python dictionary.
# It works either way!
# ============================================================

import json
import time
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

# ---- Try to import Redis ----
# If Redis is not installed, we'll use a simple dictionary instead
try:
    import redis
    REDIS_AVAILABLE = True
    print("✅ Redis library found!")
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not installed. Using in-memory cache (this is fine for development!)")


class SimpleMemoryCache:
    """
    A simple in-memory cache using a Python dictionary.
    This is our fallback when Redis is not available.
    
    Think of it like a Post-It note board in memory.
    Items expire after a set time (like Post-Its falling off).
    
    LIMITATION: This cache is wiped when the server restarts.
    Redis remembers data even after restart.
    """
    
    def __init__(self):
        # Storage: {key: {"value": data, "expires_at": timestamp}}
        self._store = {}
        print("📝 Using in-memory cache (SimpleMemoryCache)")
    
    def get(self, key: str) -> Optional[str]:
        """Get a value. Returns None if not found or expired."""
        if key not in self._store:
            return None
        
        item = self._store[key]
        
        # Check if item has expired
        if item["expires_at"] and time.time() > item["expires_at"]:
            del self._store[key]  # Clean up expired item
            return None
        
        return item["value"]
    
    def set(self, key: str, value: str, ex: int = 3600) -> bool:
        """
        Store a value.
        ex = expiry in seconds (default: 1 hour)
        """
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ex if ex else None
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Remove a key from cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists and hasn't expired."""
        return self.get(key) is not None
    
    def flushall(self):
        """Clear all cached data."""
        self._store.clear()
        return True


class CacheManager:
    """
    Smart cache that uses Redis if available, otherwise falls back to SimpleMemoryCache.
    
    You use this class the same way regardless of which backend is running.
    It handles the switching automatically!
    """
    
    def __init__(self):
        self._cache = None
        self._backend = None
        self._connect()
    
    def _connect(self):
        """Try to connect to Redis, fall back to memory cache if not available."""
        if REDIS_AVAILABLE:
            try:
                # Try to connect to Redis
                # Default: localhost port 6379 (standard Redis port)
                r = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=True,  # Return strings, not bytes
                    socket_timeout=2        # Give up after 2 seconds if Redis isn't running
                )
                r.ping()  # Test the connection
                self._cache = r
                self._backend = "redis"
                print("✅ Connected to Redis successfully!")
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}")
                print("📝 Falling back to in-memory cache...")
                self._cache = SimpleMemoryCache()
                self._backend = "memory"
        else:
            self._cache = SimpleMemoryCache()
            self._backend = "memory"
    
    @property
    def backend(self) -> str:
        """Returns which backend is being used: 'redis' or 'memory'"""
        return self._backend
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        Automatically deserializes JSON.
        """
        try:
            value = self._cache.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Store a value in cache.
        Automatically serializes to JSON.
        ttl_seconds = how long to keep it (default: 1 hour)
        """
        try:
            serialized = json.dumps(value)
            self._cache.set(key, serialized, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove a value from cache."""
        try:
            self._cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    def get_session(self, session_token: str) -> Optional[dict]:
        """Helper: Get session data from cache."""
        return self.get(f"session:{session_token}")
    
    def set_session(self, session_token: str, data: dict, ttl: int = 7200) -> bool:
        """Helper: Store session data (default 2 hours TTL)."""
        return self.set(f"session:{session_token}", data, ttl_seconds=ttl)
    
    def get_embeddings(self, text_hash: str) -> Optional[list]:
        """Helper: Get cached sentence embeddings (expensive to recompute!)."""
        return self.get(f"embedding:{text_hash}")
    
    def set_embeddings(self, text_hash: str, embeddings: list, ttl: int = 86400) -> bool:
        """Helper: Cache embeddings for 24 hours."""
        return self.set(f"embedding:{text_hash}", embeddings, ttl_seconds=ttl)
    
    def increment_answer_count(self, session_token: str) -> int:
        """Track how many answers a session has submitted."""
        key = f"answer_count:{session_token}"
        current = self.get(key) or 0
        new_count = current + 1
        self.set(key, new_count, ttl_seconds=7200)
        return new_count
    
    def get_status(self) -> dict:
        """Return info about the cache system."""
        return {
            "backend": self._backend,
            "available": self._cache is not None,
            "message": "Using Redis" if self._backend == "redis" else "Using in-memory cache (Redis not connected)"
        }


# Create ONE global instance of CacheManager
# Import this in other files: from app.utils.cache import cache
cache = CacheManager()
