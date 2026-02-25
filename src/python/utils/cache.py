import time
from typing import Any, Optional


class CacheManager:
    """A simple TTL-based cache manager to reduce redundant network requests."""
    def __init__(self, default_ttl: int = 3600):
        self._cache = {}
        self.default_ttl = default_ttl

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value in the cache with an optional TTL (seconds)."""
        expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache if it's not expired."""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        if time.time() > item["expires_at"]:
            del self._cache[key]
            return None
            
        return item["value"]

    def delete(self, key: str):
        """Remove a specific key from the cache."""
        if key in self._cache:
            return None

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
