import time
from contextlib import contextmanager


class Timings(dict):
    """Per-stage latency in milliseconds: `with timings.measure("llm"): ...`."""

    @contextmanager
    def measure(self, stage: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self[stage] = self.get(stage, 0.0) + (time.perf_counter() - start) * 1000
