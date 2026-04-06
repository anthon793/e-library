from __future__ import annotations

import asyncio
import time
from collections import defaultdict


class SimpleRateLimiter:
    def __init__(self, calls_per_second: float = 1.0):
        self.interval = 1.0 / max(calls_per_second, 0.1)
        self._locks = defaultdict(asyncio.Lock)
        self._last_call = defaultdict(float)

    async def throttle(self, key: str) -> None:
        async with self._locks[key]:
            now = time.monotonic()
            elapsed = now - self._last_call[key]
            wait_for = self.interval - elapsed
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_call[key] = time.monotonic()


rate_limiter = SimpleRateLimiter(calls_per_second=1.2)
