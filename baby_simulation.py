import random

import simpy

from config import SERVER_COUNT, SEED, SIMULATION_HOURS, RAIN_PROBABILITY
from arrivals import generate_arrivals
from results import print_results


# Start the model only when this file is run directly.
if __name__ == "__main__":
    random.seed(SEED)

    # Each value describes one hour: True means rain, False means dry weather.
    # All ships share this schedule and read only the current hour.
    rain_schedule = [
        random.random() < RAIN_PROBABILITY
        for _ in range(SIMULATION_HOURS)
    ]

    # Create the shared simulation clock and server resource.
    env = simpy.Environment()
    servers = simpy.Resource(env, capacity=SERVER_COUNT)
    records = []
    env.process(generate_arrivals(env, servers, rain_schedule, records))

    # Events at the exact end time are excluded; unfinished ships are counted separately.
    env.run(until=SIMULATION_HOURS)
    print_results(records, servers)
