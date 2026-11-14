"""Tests for fault handling and safety (REQ-11 to REQ-15)."""

import pytest

from thermostat.controller import State

INVALID_READINGS = [None, -20.1, 60.1, 999.0]


def enter_error(controller, sensor):
    """Helper: put the controller into ERROR with an overheat."""
    sensor.set_temperature(45.0)
    controller.run_for(100)
    assert controller.state is State.ERROR


# ---------- Sensor validation ----------

@pytest.mark.req("REQ-11")
@pytest.mark.parametrize("bad_reading", INVALID_READINGS)
def test_single_invalid_reading_is_ignored(controller, sensor, heater, bad_reading):
    sensor.set_temperature(19.0)
    controller.run_for(100)

    sensor.set_temperature(bad_reading)
    controller.run_for(100)

    assert controller.state is State.HEATING  # still uses the last valid 19.0
    assert heater.is_on


@pytest.mark.req("REQ-11")
@pytest.mark.parametrize("edge_reading", [-20.0, 39.9])
def test_readings_at_edge_of_valid_range_are_accepted(controller, sensor, edge_reading):
    sensor.set_temperature(edge_reading)
    controller.run_for(1000)  # 10 readings: if counted as invalid, we would reach ERROR

    assert controller.state is not State.ERROR


# ---------- Sensor fault ----------

@pytest.mark.req("REQ-12")
def test_two_invalid_readings_do_not_cause_error(controller, sensor):
    sensor.set_temperature(None)
    controller.run_for(200)

    assert controller.state is not State.ERROR


@pytest.mark.req("REQ-12")
@pytest.mark.parametrize("bad_reading", INVALID_READINGS)
def test_three_invalid_readings_cause_error(controller, sensor, heater, cooler, bad_reading):
    sensor.set_temperature(bad_reading)
    controller.run_for(300)

    assert controller.state is State.ERROR
    assert not heater.is_on
    assert not cooler.is_on


@pytest.mark.req("REQ-12")
def test_valid_reading_resets_the_fault_counter(controller, sensor):
    for reading in [None, None, 21.0, None, None]:
        sensor.set_temperature(reading)
        controller.run_for(100)

    assert controller.state is not State.ERROR


# ---------- Overheat ----------

@pytest.mark.req("REQ-13")
@pytest.mark.parametrize("temp", [40.0, 45.0])
def test_overheat_switches_heater_off_within_one_scan(controller, sensor, heater, temp):
    sensor.set_temperature(19.0)
    controller.run_for(100)
    assert heater.is_on

    sensor.set_temperature(temp)
    controller.run_for(100)

    assert controller.state is State.ERROR
    assert not heater.is_on


# ---------- Safe state ----------

@pytest.mark.req("REQ-14")
def test_error_stays_until_reset_even_when_fault_is_gone(controller, sensor, heater, cooler):
    enter_error(controller, sensor)

    sensor.set_temperature(21.0)
    controller.run_for(10_000)

    assert controller.state is State.ERROR
    assert not heater.is_on
    assert not cooler.is_on


@pytest.mark.req("REQ-14")
@pytest.mark.parametrize("temp", [15.0, 27.0])
def test_no_output_switches_on_in_error(controller, sensor, heater, cooler, temp):
    enter_error(controller, sensor)

    sensor.set_temperature(temp)  # would normally start heating or cooling
    controller.run_for(10_000)

    assert not heater.is_on
    assert not cooler.is_on


# ---------- Reset ----------

@pytest.mark.req("REQ-15")
def test_reset_returns_to_idle_when_safe(controller, sensor):
    enter_error(controller, sensor)
    sensor.set_temperature(21.0)

    assert controller.reset() is True
    assert controller.state is State.IDLE


@pytest.mark.req("REQ-15")
@pytest.mark.parametrize("reading", [40.0, 45.0, None, 999.0])
def test_reset_refused_when_not_safe(controller, sensor, reading):
    enter_error(controller, sensor)
    sensor.set_temperature(reading)

    assert controller.reset() is False
    assert controller.state is State.ERROR


@pytest.mark.req("REQ-15")
def test_reset_has_no_effect_outside_error(controller):
    assert controller.reset() is False
    assert controller.state is State.IDLE


@pytest.mark.req("REQ-15")
def test_controller_works_normally_after_reset(controller, sensor, heater):
    enter_error(controller, sensor)
    sensor.set_temperature(21.0)
    controller.reset()

    sensor.set_temperature(19.0)
    controller.run_for(100)

    assert controller.state is State.HEATING
    assert heater.is_on
