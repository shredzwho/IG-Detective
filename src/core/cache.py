import time
from typing import Any, Dict

class CacheManager:
    """A simple zero-dependency in-memory TTL cache."""
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Any:
        entry = self._cache.get(key)
        if not entry:
            return None
        
        if time.time() > entry['expires_at']:
            del self._cache[key]
            return None
            
        return entry['value']

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }

    def clear(self):
        self._cache.clear()

global_cache = CacheManager()
