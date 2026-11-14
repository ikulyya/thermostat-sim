"""Tests for normal heating and cooling control (REQ-05 to REQ-10)."""

import random

import pytest

from thermostat.controller import State


# ---------- Heating ----------

@pytest.mark.req("REQ-05")
def test_heating_starts_within_one_scan_cycle(controller, sensor, heater):
    sensor.set_temperature(20.4)
    controller.run_for(100)

    assert controller.state is State.HEATING
    assert heater.is_on


@pytest.mark.req("REQ-05")
@pytest.mark.parametrize("temp", [20.5, 21.0, 21.5])
def test_no_heating_inside_hysteresis_band(controller, sensor, heater, temp):
    sensor.set_temperature(temp)
    controller.run_for(1000)

    assert controller.state is State.IDLE
    assert not heater.is_on


@pytest.mark.req("REQ-06")
@pytest.mark.parametrize("temp", [21.0, 21.3])
def test_heating_stops_within_2_s(controller, sensor, heater, run_until, temp):
    sensor.set_temperature(19.0)
    controller.run_for(100)
    assert heater.is_on

    sensor.set_temperature(temp)
    elapsed = run_until(lambda: not heater.is_on, max_ms=2000)

    assert elapsed is not None, "heater was still ON after 2 s"
    assert controller.state is State.IDLE


@pytest.mark.req("REQ-06")
def test_heating_continues_until_setpoint_is_reached(controller, sensor, heater):
    sensor.set_temperature(19.0)
    controller.run_for(100)

    sensor.set_temperature(20.8)  # warmer, but not yet at the setpoint
    controller.run_for(1000)

    assert controller.state is State.HEATING
    assert heater.is_on


# ---------- Cooling ----------

@pytest.mark.req("REQ-07")
def test_cooling_starts_within_one_scan_cycle(controller, sensor, cooler):
    sensor.set_temperature(21.6)
    controller.run_for(100)

    assert controller.state is State.COOLING
    assert cooler.is_on


@pytest.mark.req("REQ-08")
@pytest.mark.parametrize("temp", [21.0, 20.7])
def test_cooling_stops_within_2_s(controller, sensor, cooler, run_until, temp):
    sensor.set_temperature(23.0)
    controller.run_for(100)
    assert cooler.is_on

    sensor.set_temperature(temp)
    elapsed = run_until(lambda: not cooler.is_on, max_ms=2000)

    assert elapsed is not None, "cooler was still ON after 2 s"
    assert controller.state is State.IDLE


# ---------- Mutual exclusion ----------

@pytest.mark.req("REQ-09")
def test_heater_and_cooler_never_on_together(controller, sensor, heater, cooler):
    rng = random.Random(42)  # fixed seed: the same "random" sequence every run

    for _ in range(2000):
        sensor.set_temperature(round(rng.uniform(15.0, 27.0), 1))
        controller.run_for(100)
        assert not (heater.is_on and cooler.is_on)


# ---------- Minimum off time ----------

@pytest.mark.req("REQ-10")
@pytest.mark.parametrize(
    "actuator_name, on_temp",
    [("heater", 19.0), ("cooler", 23.0)],
)
def test_minimum_off_time_of_5_s(
    controller, sensor, clock, run_until, heater, cooler, actuator_name, on_temp
):
    actuator = heater if actuator_name == "heater" else cooler

    # Switch the actuator ON, then OFF again
    sensor.set_temperature(on_temp)
    controller.run_for(100)
    assert actuator.is_on
    sensor.set_temperature(21.0)
    controller.run_for(100)
    assert not actuator.is_on

    # The condition for switching ON returns immediately
    sensor.set_temperature(on_temp)
    elapsed = run_until(lambda: actuator.is_on, max_ms=6000)

    assert elapsed is not None, f"{actuator_name} never switched back ON"
    assert elapsed >= 5000, f"{actuator_name} switched ON again after only {elapsed} ms"
