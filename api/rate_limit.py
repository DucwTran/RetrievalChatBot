import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window limiter keyed by client id (IP)."""

    def __init__(self, per_minute: int, clock=time.monotonic):
        self._limit = per_minute
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            window = self._hits[key]
            while window and window[0] <= now - 60:
                window.popleft()
            if len(window) >= self._limit:
                return False
            window.append(now)
            return True
