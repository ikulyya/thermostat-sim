"""Thermo controller: state machine and scan cycle.

Implements the behaviour defined in docs/requirements_spec.md. Comments reference requirement IDs (REQ-xx) for traceability.
"""

from enum import Enum
from thermostat.actuators import Actuator
from thermostat.clock import SimClock
from thermostat.sensor import TemperatureSensor

# Parameters from section 3 of the requirements spec.

SCAN_CYCLE_MS = 100
DEFAULT_SETPOINT = 21.0
SETPOINT_MIN = 10.0
SETPOINT_MAX = 30.0
HYSTERESIS = 0.5
SENSOR_MIN = -20.0
SENSOR_MAX = 60.0
SENSOR_FAULT_LIMIT = 3
OVERHEAT_LIMIT = 40.0
MIN_OFF_TIME_MS = 5000

class State(Enum):
    IDLE = "IDLE"
    HEATING = "HEATING"
    COOLING = "COOLING" 
    ERROR = "ERROR"

class Controller:
    """reads teh sensor, decides the sate and drives the heater and cooler."""

    def __init__(
            self,
            clock: SimClock,
            sensor: TemperatureSensor,
            heater: Actuator,
            cooler: Actuator,
    ):
        self.clock = clock
        self.sensor = sensor
        self.heater = heater
        self.cooler = cooler 

        self.state = State.IDLE # REQ-01
        self.setpoint = DEFAULT_SETPOINT # REQ-03
        self.last_valid_temp: float | None = None
        self.invalid_count = 0

        self._apply_outputs()# REQ-01: outputs OFF at startup

        # Public Interface 

    def set_setpoint(self, value: float) -> bool:
        """Change the setpoint. Returns False and keeps the old one if out of range. """
        if SETPOINT_MIN <= value <= SETPOINT_MAX: #REQ-03 
            self.setpoint = value
            return True
        return False # REQ-04

    def reset(self) -> bool:
        """ Manual reset from ERROR. Returns True if the controller went back to IDLE"""
        if self.state is not State.ERROR:
            return False 
        reading = self.sensor.read()
        if self._is_valid(reading) and reading < OVERHEAT_LIMIT:
            self.state = State.IDLE
            self.invalid_count = 0
            self.last_valid_temp = reading 
            return True
        return False

    def scan(self) -> None:
        """One scan cycle"""
        temp = self._read_sensor()
        self._update_state(temp)
        self._apply_outputs()

    def run_for(self, ms: int) -> None:
        """Let `ms` milliseconds of simulated time pass, scanning every 100 ms (REQ-02)."""
        if ms % SCAN_CYCLE_MS != 0:
            raise ValueError(f"Duration must be a multiple of {SCAN_CYCLE_MS} ms")
        for _ in range(ms // SCAN_CYCLE_MS):
            self.clock.advance(SCAN_CYCLE_MS)
            self.scan()

    def _read_sensor(self) -> float | None:
        """Validate the reading and return the temperature to use (REQ-11)."""
        reading = self.sensor.read()
        if self._is_valid(reading):
            self.invalid_count = 0
            self.last_valid_temp = reading
        else:
            self.invalid_count += 1  # single bad reading: keep last valid value
        return self.last_valid_temp


    def _update_state(self, temp: float | None) -> None:
        """Decide the next state. This is the state machine from section 4 of the spec."""
        if self.state is State.ERROR:
            return  # REQ-14: only reset() can leave ERROR

        if self.invalid_count >= SENSOR_FAULT_LIMIT:  # REQ-12
            self.state = State.ERROR
            return

        if temp is None:
            return  # no valid reading yet since startup: stay as we are

        if temp >= OVERHEAT_LIMIT:  # REQ-13
            self.state = State.ERROR
            return

        if self.state is State.IDLE:
            if temp < self.setpoint - HYSTERESIS and self._can_turn_on(self.heater):
                self.state = State.HEATING  # REQ-05, REQ-10
            elif temp > self.setpoint + HYSTERESIS and self._can_turn_on(self.cooler):
                self.state = State.COOLING  # REQ-07, REQ-10

        elif self.state is State.HEATING:
            if temp >= self.setpoint:
                self.state = State.IDLE  # REQ-06

        elif self.state is State.COOLING:
            if temp <= self.setpoint:
                self.state = State.IDLE  # REQ-08

    def _apply_outputs(self) -> None:
        """Set the heater and cooler to match the state. Always switch OFF before ON (REQ-09)."""
        now = self.clock.now_ms
        if self.state is State.HEATING:
            self.cooler.turn_off(now)
            self.heater.turn_on()
        elif self.state is State.COOLING:
            self.heater.turn_off(now)
            self.cooler.turn_on()
        else:  # IDLE and ERROR: everything off (REQ-14)
            self.heater.turn_off(now)
            self.cooler.turn_off(now)

    def _can_turn_on(self, actuator: Actuator) -> bool:
        """REQ-10: has the actuator been off for at least 5 s?"""
        if actuator.last_off_ms is None:
            return True  # never switched off before
        return self.clock.now_ms - actuator.last_off_ms >= MIN_OFF_TIME_MS

    @staticmethod
    def _is_valid(reading: float | None) -> bool:
        """REQ-11: a reading is valid if it exists and is within -20..60 °C."""
        return reading is not None and SENSOR_MIN <= reading <= SENSOR_MAX
        