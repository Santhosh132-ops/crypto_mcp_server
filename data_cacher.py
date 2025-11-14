import time
from typing import Any, Dict, Optional

# Define the default cache expiration time (5 seconds for real-time data)
DEFAULT_TTL_SECONDS = 5

class DataCacher:
    """
    Simple in-memory cache with Time-To-Live (TTL) functionality.

    This prevents excessive calls to the external cryptocurrency API,
    adhering to best practices for rate-limiting and efficiency.
    """
    def __init__(self, default_ttl: int = DEFAULT_TTL_SECONDS):
        # Cache storage: {key: (timestamp_ms, ttl_ms, data)}
        self._cache: Dict[str, tuple[int, int, Any]] = {}
        self.default_ttl_ms = default_ttl * 1000  # Convert to milliseconds

    def _get_current_time_ms(self) -> int:
        """Returns the current time in milliseconds."""
        return int(time.time() * 1000)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves data from the cache if it hasn't expired.
        """
        if key in self._cache:
            timestamp, ttl_ms, data = self._cache[key]
            current_time = self._get_current_time_ms()
            
            # Check for expiration (current time > timestamp + ttl_ms)
            if current_time < timestamp + ttl_ms:
                return data
            else:
                # Item expired, remove it
                del self._cache[key]
        
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """
        Stores data in the cache with the current timestamp.
        """
        timestamp = self._get_current_time_ms()
        # Use custom TTL if provided, otherwise use default
        ttl_ms = (ttl * 1000) if ttl is not None else self.default_ttl_ms
        self._cache[key] = (timestamp, ttl_ms, data)

    def clear(self):
        """Clears all entries from the cache."""
        self._cache.clear()

# Global instance for use across the application
CACHE = DataCacher()
