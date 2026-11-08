"""Simulated temperature sensor with fault injection"""
class TemperatureSensor:
    """Returns the room temperature in °C, or None if no reading is available.

    Tests set the reading directly, including faulty values, to check
    how the controller reacts. This is called fault injection.
    """

    def __init__(self, initial_temp: float | None = 21.0):
        self._value = initial_temp

    def set_temperature(self, value: float | None) -> None:
        """Set what the next read() returns. None means the sensor gave no reading.""" 
        self._value = value

    def read(self) -> float | None:
        """Return the current reading exactly as the sensor reports it."""
        return self._value