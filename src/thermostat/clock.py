"""Simulated clock.

The simulator never uses real time. Tests move time forward by hand,
so they run instantly and give the same result every time.
"""

class SimClock:
    """ A Clock that only moves when told to"""
    def __init__(self, start_ms: int = 0):
        self._now_ms = start_ms

    @property 
    def now_ms(self) -> int:
        return self._now_ms

    def advance(self, ms: int) -> None:
        """Move time forward by `ms` milliseconds"""
        if ms < 0:
            raise ValueError("Time cannoct go backwards")
        self._now_ms += ms

    