"""Tests for in-memory cache."""

import time
import pytest
from app.services.cache import InMemoryCache


def test_cache_hit():
    """Test cache returns value within TTL."""
    cache = InMemoryCache(ttl_seconds=60)

    cache.set("test_key", {"data": "value"})
    result = cache.get("test_key")

    assert result == {"data": "value"}


def test_cache_miss_expired():
    """Test cache returns None after TTL expires."""
    cache = InMemoryCache(ttl_seconds=1)

    cache.set("test_key", {"data": "value"})
    time.sleep(1.1)
    result = cache.get("test_key")

    assert result is None


def test_cache_miss_not_found():
    """Test cache returns None for non-existent key."""
    cache = InMemoryCache(ttl_seconds=60)

    result = cache.get("nonexistent")

    assert result is None


def test_cache_clear():
    """Test cache clear removes all entries."""
    cache = InMemoryCache(ttl_seconds=60)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_make_key():
    """Test cache key generation."""
    key = InMemoryCache.make_key("EUR", "USD", "2025-07-01", "2025-07-03")

    assert key == "EUR_USD_2025-07-01_2025-07-03"


def test_cache_overwrite():
    """Test cache overwrites existing key."""
    cache = InMemoryCache(ttl_seconds=60)

    cache.set("test_key", "old_value")
    cache.set("test_key", "new_value")
    result = cache.get("test_key")

    assert result == "new_value"
