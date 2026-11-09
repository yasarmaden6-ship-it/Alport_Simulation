import random

from config import ARRIVAL_PROBABILITY, SIMULATION_HOURS
from port import ship_process


# Create at most one ship per hour and schedule its port process.
def generate_arrivals(env, berths, rain_schedule, records):
    ship_id = 0
    for _ in range(SIMULATION_HOURS):
        if random.random() < ARRIVAL_PROBABILITY:
            ship_id += 1
            # Each ship has its own process within the shared environment.
            env.process(ship_process(env, ship_id, berths, rain_schedule, records))

        # Only the arrival process waits here; existing ships can continue.
        yield env.timeout(1)
