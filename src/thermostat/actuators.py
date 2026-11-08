"""Simulated actuators: outputs that are either ON or OFF."""

class Actuatos:
    """Heated or cooler. Remembers when it was last switched off."""

    def __init__(self, name: str):
        self.name = name
        self.is_on = False
        self.last_off_ms: int | None = None

    def turn_on(self) -> None:
        self.is_on = True

    def turn_off(self, now_ms: int) -> None:
        """Switch off and reocrd the time, but only if it was actually on."""
        if self.is_on:
            self.last_off_ms = now_ms
        self.is_on = False 

    def __repr__(self) -> str:
        state = "ON" if self.is_on else "OFF"
        return f"Actuator({self.name}: {state})"