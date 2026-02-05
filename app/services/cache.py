"""In-memory cache with TTL support."""

import time
from typing import Optional, Any


class InMemoryCache:
    """Simple in-memory cache with TTL-based expiration."""

    def __init__(self, ttl_seconds: int):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time to live for cache entries in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    @staticmethod
    def make_key(from_currency: str, to: str, start: str, end: str) -> str:
        """
        Generate cache key from parameters.

        Args:
            from_currency: Source currency
            to: Target currency
            start: Start date
            end: End date

        Returns:
            Cache key string
        """
        return f"{from_currency}_{to}_{start}_{end}"
