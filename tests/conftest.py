"""Shared pytest fixtures.

Every test gets a brand-new clock, sensor, heater, cooler and controller,
so tests never affect each other.
"""

import pytest

from thermostat.actuators import Actuator
from thermostat.clock import SimClock
from thermostat.controller import SCAN_CYCLE_MS, Controller
from thermostat.sensor import TemperatureSensor


@pytest.fixture
def clock():
    return SimClock()


@pytest.fixture
def sensor():
    return TemperatureSensor(initial_temp=21.0)


@pytest.fixture
def heater():
    return Actuator("heater")


@pytest.fixture
def cooler():
    return Actuator("cooler")


@pytest.fixture
def controller(clock, sensor, heater, cooler):
    return Controller(clock, sensor, heater, cooler)


@pytest.fixture
def run_until(controller, clock):
    """Run one scan cycle at a time until `condition()` is true.

    Returns how many milliseconds it took, or None if it did not happen
    within `max_ms`. Used to test timing requirements like "within 2 s".
    """

    def _run_until(condition, max_ms):
        start = clock.now_ms
        while clock.now_ms - start < max_ms:
            controller.run_for(SCAN_CYCLE_MS)
            if condition():
                return clock.now_ms - start
        return None

    return _run_until
