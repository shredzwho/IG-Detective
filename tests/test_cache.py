import time
import pytest
from src.python.utils.cache import CacheManager

def test_cache_set_get():
    cache = CacheManager(default_ttl=10)
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_cache_expiration():
    cache = CacheManager(default_ttl=1)
    cache.set("key", "value")
    time.sleep(1.1)
    assert cache.get("key") is None

def test_cache_delete():
    cache = CacheManager()
    cache.set("key", "value")
    cache.delete("key")
    assert cache.get("key") is None

def test_cache_clear():
    cache = CacheManager()
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.clear()
    assert cache.get("k1") is None
    assert cache.get("k2") is None
