import random
from math import isfinite

import simpy

from arrivals import generate_arrivals
from config import (
    INITIAL_WET,
    OPERATION_HOURS,
    SEED,
    SERVER_COUNT,
    SIMULATION_HOURS,
    SIMULATION_START,
    WEATHER_SEED,
)
from port import Port
from results import print_results
from weather import generate_weather


def run_simulation(log_events=False):
    if not isfinite(SIMULATION_HOURS) or SIMULATION_HOURS <= 0:
        raise ValueError(
            "Simulation hours must be a positive finite number."
        )

    random.seed(SEED)

    weather = generate_weather(
        SIMULATION_START,
        SIMULATION_HOURS,
        INITIAL_WET,
        WEATHER_SEED,
    )

    env = simpy.Environment()

    port = Port(
        env,
        SERVER_COUNT,
        weather,
        log_events=log_events,
        operation_hours=OPERATION_HOURS,
        end_hour=SIMULATION_HOURS,
    )

    env.process(generate_arrivals(env, port, until=SIMULATION_HOURS))
    env.run(until=SIMULATION_HOURS)

    while env.peek() == SIMULATION_HOURS:
        env.step()

    return port


if __name__ == "__main__":
    print_results(run_simulation())