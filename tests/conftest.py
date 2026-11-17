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


# ---------- Requirement traceability ----------
#
# Every test is labelled with @pytest.mark.req("REQ-xx").
# The hooks below collect results per requirement, print a coverage
# summary at the end of the run, and add a "Requirement" column to
# the pytest-html report.

ALL_REQUIREMENTS = [f"REQ-{n:02d}" for n in range(1, 16)]
_results = {req: {"passed": 0, "failed": 0} for req in ALL_REQUIREMENTS}


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """Runs after each test phase: remember which requirement the test covers."""
    report = yield
    marker = item.get_closest_marker("req")
    report.req = marker.args[0] if marker else ""

    counts = report.when == "call" or (report.when == "setup" and report.failed)
    if counts and report.req in _results:
        _results[report.req]["passed" if report.passed else "failed"] += 1
    return report


def pytest_terminal_summary(terminalreporter):
    """Print a requirement coverage table after the test run."""
    tr = terminalreporter
    tr.section("Requirement coverage")
    for req, counts in _results.items():
        total = counts["passed"] + counts["failed"]
        if total == 0:
            status = "NOT TESTED"
        elif counts["failed"]:
            status = "FAIL"
        else:
            status = "PASS"
        tr.write_line(f"{req}  {status:<10}  {counts['passed']}/{total} tests passed")

    untested = [req for req, c in _results.items() if c["passed"] + c["failed"] == 0]
    if untested:
        tr.write_line(f"Requirements without tests: {', '.join(untested)}", red=True, bold=True)


def pytest_sessionfinish(session, exitstatus):
    """Fail the whole run if any requirement has no tests (only on a full run)."""
    ran_everything = not session.config.option.keyword and not session.config.option.markexpr
    untested = [req for req, c in _results.items() if c["passed"] + c["failed"] == 0]
    if ran_everything and untested and session.testscollected > 0 and exitstatus == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(1, "<th>Requirement</th>")


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    cells.insert(1, f"<td>{getattr(report, 'req', '')}</td>")
