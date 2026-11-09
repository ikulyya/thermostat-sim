"""Manual demo: runs the thermostat through a short scenario and prints what happens."""

from thermostat.actuators import Actuator
from thermostat.clock import SimClock
from thermostat.controller import Controller
from thermostat.sensor import TemperatureSensor

clock = SimClock()
sensor = TemperatureSensor(initial_temp=21.0)
heater = Actuator("heater")
cooler = Actuator("cooler")
controller = Controller(clock, sensor, heater, cooler)


scenario = [
    ("Room is comfortable", 21.0),
    ("Room gets cold", 19.0),
    ("Room warms to setpoint", 21.0),
    ("Room gets hot", 23.0),
    ("Room cools down", 20.9),
    ("Sensor glitch (1 reading)", None),
    ("Overheat!", 41.0),
    ("Temperature back to normal", 21.0),
]


for description, temp in scenario:
    sensor.set_temperature(temp)
    controller.run_for(100 if temp is None else 1000)
    print(
        f"t={clock.now_ms / 1000:5.1f}s  {description:<27} "
        f"T={str(temp):>5}  state={controller.state.name:<8} {heater} {cooler}"
    )

print("Manual reset accepted:", controller.reset())
print("State after reset:", controller.state.name)
