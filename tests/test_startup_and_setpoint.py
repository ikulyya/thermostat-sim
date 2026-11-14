"""Tests for startup, scan cycle and setpoint handling (REQ-01 to REQ-04)."""

import pytest

from thermostat.controller import State


@pytest.mark.req("REQ-01")
def test_starts_in_idle_with_outputs_off(controller, heater, cooler):
    assert controller.state is State.IDLE
    assert not heater.is_on
    assert not cooler.is_on


@pytest.mark.req("REQ-02")
def test_scans_every_100_ms(controller, clock, monkeypatch):
    scan_times = []
    original_scan = controller.scan

    def recording_scan():
        scan_times.append(clock.now_ms)
        original_scan()

    monkeypatch.setattr(controller, "scan", recording_scan)
    controller.run_for(1000)

    assert scan_times == [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]


@pytest.mark.req("REQ-02")
def test_run_for_rejects_partial_scan_cycle(controller):
    with pytest.raises(ValueError):
        controller.run_for(150)


@pytest.mark.req("REQ-03")
def test_default_setpoint_is_21(controller):
    assert controller.setpoint == 21.0


@pytest.mark.req("REQ-03")
@pytest.mark.parametrize("value", [10.0, 21.5, 30.0])
def test_valid_setpoint_is_accepted(controller, value):
    assert controller.set_setpoint(value) is True
    assert controller.setpoint == value


@pytest.mark.req("REQ-04")
@pytest.mark.parametrize("value", [9.9, 30.1, -5.0, 100.0])
def test_invalid_setpoint_is_rejected_and_old_one_kept(controller, value):
    controller.set_setpoint(25.0)

    assert controller.set_setpoint(value) is False
    assert controller.setpoint == 25.0
