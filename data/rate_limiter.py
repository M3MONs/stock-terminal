from __future__ import annotations

import threading
import time


class RateLimiter:
    def __init__(self, max_per_minute: int = 8) -> None:
        self._max = max_per_minute
        self._window = 60.0
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.time()
            self._calls = [t for t in self._calls if now - t < self._window]
            if len(self._calls) >= self._max:
                wait_sec = self._window - (now - self._calls[0])
                if wait_sec > 0:
                    time.sleep(wait_sec)
                self._calls.pop(0)
            self._calls.append(time.time())
